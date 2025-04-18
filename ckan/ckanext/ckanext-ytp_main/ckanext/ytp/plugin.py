import json
import logging

import six
import iso8601
import re
import urllib
import sqlalchemy
import ckan.lib.base as base
from . import logic as plugin_logic, hierarchy as plugin_hierarchy
import ckan.plugins as p
from ckan import authz as authz

from ckan import plugins, model, logic
from ckan.common import _, c, request, is_flask_request

from ckan.lib import helpers
from ckan.lib.munge import munge_title_to_name
from ckan.lib.navl.dictization_functions import Missing, Invalid
from ckan.lib.plugins import DefaultOrganizationForm, DefaultTranslation, DefaultPermissionLabels
from ckan.logic import NotFound, get_action, check_access
from ckan.model import Session
from ckan.plugins import toolkit, plugin_loaded
from ckan.plugins.toolkit import config, chained_action
from ckanext.report.interfaces import IReport

from ckanext.sitesearch.interfaces import ISiteSearch
from ckanext.showcase.model import ShowcaseAdmin
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import false

from ckanext.ytp.logic import package_autocomplete, store_municipality_bbox_data, dcat_catalog_show
import ckanext.ytp.views as views
from ckanext.ytp import auth, menu, cli, validators, views_organization

from .helpers import extra_translation, render_date, service_database_enabled, get_json_value, \
    sort_datasets_by_state_priority, get_facet_item_count, get_remaining_facet_item_count, sort_facet_items_by_name, \
    get_sorted_facet_items_dict, calculate_dataset_stars, get_upload_size, get_license, \
    get_geonetwork_link, calculate_metadata_stars, get_tooltip_content_types, unquote_url, \
    sort_facet_items_by_count, scheming_field_only_default_required, add_locale_to_source, \
    scheming_language_text_or_empty, get_lang_prefix, call_toolkit_function, get_translation, get_translated, \
    dataset_display_name, resource_display_name, get_current_date, parse_datetime, get_label_for_producer, \
    scheming_category_list, check_group_selected, group_title_by_id, group_list_with_selected, \
    get_last_harvested_date, get_resource_sha256, get_package_showcase_list, get_apiset_package_list, \
    get_groups_where_user_is_admin, get_value_from_extras_by_key, get_field_from_dataset_schema, \
    get_field_from_resource_schema, is_boolean_selected, site_url_with_root_path, \
    get_organization_filters_count, package_count_for_source_customized, group_tree_section, \
    get_highvalue_category_label, scheming_highvalue_category_list

from .tools import create_system_context

from ckan.logic.validators import tag_length_validator, tag_name_validator

try:
    from collections import OrderedDict  # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

from ckan.plugins.toolkit import ValidationError


# This plugin is designed to work only these versions of CKAN
plugins.toolkit.check_ckan_version(min_version='2.0')

abort = base.abort
log = logging.getLogger(__name__)


OPEN_DATA = 'Open Data'
INTEROPERABILITY_TOOLS = 'Interoperability Tools'
PUBLIC_SERVICES = 'Public Services'

ISO_DATETIME_FORMAT = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}$')

_category_mapping = {
    'alueet-ja-kaupungit': ['imagery base maps earth cover', 'planning cadastre', 'structure', 'imageryBaseMapsEarthCover',
                            'planningCadastre'],
    'energia': [],
    'valtioneuvosto-ja-julkinen-sektori': [],
    'kansainvaliset-kysymykset': [],
    'koulutus-kulttuuri-ja-urheilu': [],
    'liikenne': ['transportation'],
    'maatalous-kalastus-metsatalous-ja-elintarvikkeet': ['farming'],
    'oikeus-oikeusjarjestelma-ja-yleinen-turvallisuus': ['intelligence military', 'intelligenceMilitary'],
    'rakennettu-ymparisto-ja-infrastruktuuri': ['boundaries', 'elevation', 'imagery base maps earth cover', 'location',
                                                'planning cadastre', 'structure', 'utilities communication',
                                                'imageryBaseMapsEarthCover', 'planningCadastre', 'utilitiesCommunication'],
    'talous-ja-raha-asiat': ['economy'],
    'terveys': ['health'],
    'tiede-ja-teknologia': ['geoscientific information', 'geoscientificInformation'],
    'vaesto-ja-yhteiskunta': ['society'],
    'ymparisto': ['biota', 'elevation', 'environment', 'geoscientific information', 'imagery base maps earth cover',
                  'inland waters', 'oceans', 'climatology, meteorology, atmosphere', 'geoscientificInformation',
                  'imageryBaseMapsEarthCover', 'inlandWaters', 'climatologyMeteorologyAtmosphere']
}


class YtpMainTranslation(DefaultTranslation):

    def i18n_domain(self):
        return "ckanext-ytp_main"


class OpendataCliPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IClick)

    # IClick

    def get_commands(self):
        return cli.get_commands()


def create_vocabulary(name, defer=False):
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    try:
        data = {'id': name}
        return toolkit.get_action('vocabulary_show')(context, data)
    except NotFound:
        pass

    log.info("Creating vocab '" + name + "'")
    data = {'name': name}
    try:
        if defer:
            context['defer_commit'] = True
        return toolkit.get_action('vocabulary_create')(context, data)
    except Exception as e:
        log.error('%s' % e)


def create_tag_to_vocabulary(tag, vocab, defer=False):
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    data = {'id': vocab}
    v = toolkit.get_action('vocabulary_show')(context, data)

    data = {
        "name": tag,
        "vocabulary_id": v['id']}

    if defer:
        context['defer_commit'] = True
    try:
        toolkit.get_action('tag_create')(context, data)
    except ValidationError:
        pass


def _escape(value):
    return urllib.parse.quote(six.text_type(value))


def _prettify(field_name):
    """ Taken from ckan.logic.ValidationError.error_summary """
    field_name = re.sub('(?<!\\w)[Uu]rl(?!\\w)', 'URL', field_name.replace('_', ' ').capitalize())
    return _(field_name.replace('_', ' '))


@chained_action
@logic.side_effect_free
def action_package_show(original_action, context, data_dict):
    result = original_action(context, data_dict)
    organization_data = result.get('organization', None)
    if organization_data:
        organization_id = organization_data.get('id', None)
        if organization_id:
            group = model.Group.get(organization_id)
            result['organization'].update(group.extras)

    return result


@chained_action
@logic.side_effect_free
def action_package_search(original_action, context, data_dict):
    # sort by the given sorting option or by relevancy
    data_dict['sort'] = data_dict.get('sort') or 'score desc, metadata_created desc'
    return original_action(context, data_dict)


@logic.side_effect_free
def statistics(context, data_dict):

    datasets = toolkit.get_action('package_search')({}, {'rows': 0})

    apisets = len(toolkit.get_action('apiset_list')({}, {'all_fields': False})) if plugin_loaded('apis') else 0
    organizations = toolkit.get_action('organization_list')({}, {})
    showcases = len(toolkit.get_action('ckanext_showcase_list')({}, {'all_fields': False})) \
        if plugin_loaded('sixodp_showcase') else 0

    return {
        'datasets': datasets['count'],
        'apisets': apisets,
        'organizations': len(organizations),
        'showcases': showcases
    }


class YTPDatasetForm(plugins.SingletonPlugin, toolkit.DefaultDatasetForm, YtpMainTranslation):
    plugins.implements(plugins.interfaces.IFacets, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IBlueprint)

    _localized_fields = ['title', 'notes', 'copyright_notice']

    _key_exclude = ['resources', 'organization', 'copyright_notice', 'license_url', 'name',
                    'version', 'state', 'notes', 'tags', 'title', 'collection_type', 'license_title', 'extra_information',
                    'maintainer', 'author', 'owner', 'num_tags', 'owner_org', 'type', 'license_id', 'num_resources',
                    'temporal_granularity', 'temporal_coverage_from', 'temporal_coverage_to', 'update_frequency']

    _key_exclude_resources = ['description', 'name', 'temporal_coverage_from', 'temporal_coverage_to', 'url_type',
                              'mimetype', 'resource_type', 'mimetype_inner', 'update_frequency', 'last_modified',
                              'format', 'temporal_granularity', 'url', 'webstore_url', 'position', 'created',
                              'webstore_last_updated', 'cache_url', 'cache_last_updated', 'size']

    auto_author = False

    # IConfigurable #

    def configure(self, config):
        self.auto_author = toolkit.asbool(config.get('ckanext.ytp.auto_author', False))

    # ITranslation #

    def i18n_domain(self):
        return "ckanext-ytp_main"

    # IRoutes #

    def before_map(self, m):
        health_controller = 'ckanext.ytp.health:HealthController'
        m.connect('/health', action='check', controller=health_controller)
        """ Override ckan api for autocomplete """
        controller = 'ckanext.ytp.controller:YtpDatasetController'
        m.connect('/api/2/util/tag/autocomplete', action='ytp_tag_autocomplete',
                  controller=controller,
                  conditions=dict(method=['GET']))
        m.connect('/api/util/dataset/autocomplete', action='dataset_autocomplete',
                  controller=controller,
                  conditions=dict(method=['GET']))
        m.connect('/dataset/new_metadata/{id}', action='new_metadata',
                  controller=controller)  # override metadata step at new package
        # m.connect('dataset_edit', '/dataset/edit/{id}',
        # action='edit', controller=controller, ckan_icon='edit')
        # m.connect('new_resource', '/dataset/new_resource/{id}',
        # action='new_resource', controller=controller, ckan_icon='new')
        m.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}', action='resource_edit',
                  controller=controller, ckan_icon='edit')

        # Mapping of new dataset is needed since, remapping on read overwrites it
        m.connect('add dataset', '/dataset/new', controller='package', action='new')
        m.connect('/dataset/{id}.{format}', action='read', controller=controller)
        m.connect('related_new', '/dataset/{id}/related/new', action='new_related', controller=controller)
        m.connect('related_edit', '/dataset/{id}/related/edit/{related_id}',
                  action='edit_related', controller=controller)
        # m.connect('dataset_read', '/dataset/{id}', action='read', controller=controller, ckan_icon='sitemap')
        m.connect('dataset_groups', '/dataset/groups/{id}', action="groups", controller=controller)
        m.connect('/api/util/dataset/autocomplete_by_collection_type', action='autocomplete_packages_by_collection_type',
                  controller=controller)
        return m

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('public/javascript/', 'ytp_common_js')
        toolkit.add_resource('public/css/', 'ytp_common_css')
        toolkit.add_template_directory(config, '../common/templates')

    # IDatasetForm

    def package_types(self):
        return []

    def is_fallback(self):
        return True

    def _get_collection_type(self):
        """Gets the type of collection (Open Data, Interoperability Tools, or Public Services).
        This method can be used to identify which collection the user is currently looking at or editing,
        i.e., which page the user is on.
        """
        collection_type = request.params.get('collection_type', None)
        if not collection_type and c.pkg_dict and 'collection_type' in c.pkg_dict:
            collection_type = c.pkg_dict['collection_type']
        return collection_type

    def new_template(self):
        return 'package/new.html'

    # IFacets #

    def dataset_facets(self, facets_dict, package_type):
        lang = get_lang_prefix()
        facets_dict = OrderedDict()
        # use different ordering for apisets
        if package_type == 'apiset':
            facets_dict['vocab_keywords_' + lang] = _('Tags')
            facets_dict['organization'] = _('Organization')
            facets_dict['res_format'] = _('Formats')
            facets_dict['license_id'] = _('Licenses')
            facets_dict['groups'] = _('Category')
            facets_dict['producer_type'] = _('Producer type')
        else:
            facets_dict['vocab_international_benchmarks'] = _('International Benchmarks')
            facets_dict['vocab_geographical_coverage'] = _('Geographical coverage')
            facets_dict['collection_type'] = _('Collection Types')
            facets_dict['vocab_keywords_' + lang] = _('Tags')
            facets_dict['organization'] = _('Organization')
            facets_dict['res_format'] = _('Formats')
            facets_dict['license_id'] = _('Licenses')
            facets_dict['groups'] = _('Category')
            facets_dict['producer_type'] = _('Producer type')
            facets_dict['vocab_highvalue_category'] = _('High-value dataset category')
            # add more dataset facets here

        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        lang = get_lang_prefix()
        facets_dict = OrderedDict()
        facets_dict.update({'collection_type': _('Collection Types')})
        facets_dict['vocab_keywords_' + lang] = _('Tags')
        facets_dict.update({'vocab_content_type': _('Content Types')})
        facets_dict.update({'res_format': _('Formats')})

        return facets_dict

    # ITemplateHelpers #

    def _unique_formats(self, resources, package_type='dataset'):
        formats = set()
        for resource in resources:
            if package_type == 'apiset':
                for format in resource.get('formats', '').split(','):
                    formats.add(format)
            else:
                formats.add(resource.get('format'))
        formats.discard('')
        return formats

    def _current_user(self):
        return c.userobj

    def _get_user_by_id(self, user_id):
        if not user_id:
            return None
        else:
            user = model.User.get(user_id)
            return user.name

    def _get_user(self, user):
        if not isinstance(user, model.User):
            user_name = six.text_type(user)
            user = model.User.get(user_name)
            if not user:
                return user_name
        if user:
            name = user.name if model.User.VALID_NAME.match(user.name) else user.id
            display_name = user.display_name
            url = helpers.url_for(controller='user', action='read', id=name)
            return {'name': name, 'display_name': display_name, 'url': url}

    def _resource_display_name(self, resource_dict):
        """ taken from helpers.resource_display_name """
        value = resource_display_name(resource_dict)
        return value if value != _("Unnamed resource") else _("Additional Info")

    def _auto_author_set(self):
        return self.auto_author

    def _is_sysadmin(self):
        if c.userobj:
            return c.userobj.sysadmin
        return False

    def _is_loggedinuser(self):
        return authz.auth_is_loggedin_user()

    def get_helpers(self):
        return {'current_user': self._current_user,
                'get_user': self._get_user,
                'unique_formats': self._unique_formats,
                'extra_translation': extra_translation,
                'service_database_enabled': service_database_enabled,
                'resource_display_name': self._resource_display_name,
                'auto_author_set': self._auto_author_set,
                'get_json_value': get_json_value,
                'sort_datasets_by_state_priority': sort_datasets_by_state_priority,
                'get_facet_item_count': get_facet_item_count,
                'get_remaining_facet_item_count': get_remaining_facet_item_count,
                'sort_facet_items_by_name': sort_facet_items_by_name,
                'sort_facet_items_by_count': sort_facet_items_by_count,
                'get_sorted_facet_items_dict': get_sorted_facet_items_dict,
                'calculate_dataset_stars': calculate_dataset_stars,
                'calculate_metadata_stars': calculate_metadata_stars,
                'is_sysadmin': self._is_sysadmin,
                'is_loggedinuser': self._is_loggedinuser,
                'get_upload_size': get_upload_size,
                'render_date': render_date,
                'get_license': get_license,
                'get_current_date': get_current_date,
                'parse_datetime': parse_datetime,
                'get_geonetwork_link': get_geonetwork_link,
                'get_tooltip_content_types': get_tooltip_content_types,
                'unquote_url': unquote_url,
                'scheming_field_only_default_required': scheming_field_only_default_required,
                'add_locale_to_source': add_locale_to_source,
                'scheming_language_text_or_empty': scheming_language_text_or_empty,
                'get_lang_prefix': get_lang_prefix,
                'call_toolkit_function': call_toolkit_function,
                'get_translation': get_translation,
                'get_translated': get_translated,
                'dataset_display_name': dataset_display_name,
                'group_title_by_id': group_title_by_id,
                'get_label_for_producer': get_label_for_producer,
                'scheming_category_list': scheming_category_list,
                'check_group_selected': check_group_selected,
                'group_list_with_selected': group_list_with_selected,
                'get_resource_sha256': get_resource_sha256,
                'get_package_showcase_list': get_package_showcase_list,
                'get_apiset_package_list': get_apiset_package_list,
                'get_groups_where_user_is_admin': get_groups_where_user_is_admin,
                'get_value_from_extras_by_key': get_value_from_extras_by_key,
                'get_field_from_dataset_schema': get_field_from_dataset_schema,
                'get_field_from_resource_schema': get_field_from_resource_schema,
                "is_boolean_selected": is_boolean_selected,
                'site_url_with_root_path': site_url_with_root_path,
                'get_organization_filters_count': get_organization_filters_count,
                'asbool': toolkit.asbool,
                'package_count_for_source_customized': package_count_for_source_customized,
                'scheming_highvalue_category_list': scheming_highvalue_category_list,
                'get_highvalue_category_label': get_highvalue_category_label
                }

    def get_auth_functions(self):
        return {'related_update': auth.related_update,
                'related_create': auth.related_create,
                'package_update': auth.package_update,
                'allowed_to_view_user_list': auth.user_list}

        # IPackageController #

    def after_show(self, context, pkg_dict):
        if 'resources' in pkg_dict and pkg_dict['resources']:
            for resource in pkg_dict['resources']:
                if 'url_type' in resource and isinstance(resource['url_type'], Missing):
                    resource['url_type'] = None

        if (pkg_dict.get('groups', None)):
            translation_dict = {
                'all_fields': True,
                'include_extras': True,
                'groups': [ group.get('name') for group in pkg_dict.get('groups') ]
            }

            group_context = context.copy()

            # Schema should be none for group_list -> group_show calls,
            # otherwise it will produce an error as dataset schema is wrong for this
            group_context.pop('schema', None)

            pkg_dict['groups'] = get_action('group_list')(group_context, translation_dict)

    def before_index(self, pkg_dict):
        if 'tags' in pkg_dict:
            tags = pkg_dict['tags']
            if tags:
                pkg_dict['tags'] = [tag.lower() for tag in tags]

        if 'vocab_content_type' in pkg_dict:
            content_types = pkg_dict['vocab_content_type']
            if content_types:
                pkg_dict['vocab_content_type'] = [content_type.lower() for content_type in content_types]

        if 'res_format' in pkg_dict:
            res_formats = pkg_dict['res_format']
            if res_formats:
                pkg_dict['res_format'] = [res_format.lower() for res_format in res_formats]

        # Converting from creator_user_id to source. Grouping users default and harvest into harvesters and manual to the rest
        if 'creator_user_id' in pkg_dict:
            user_id = pkg_dict['creator_user_id']
            if user_id:
                user_name = self._get_user_by_id(user_id)
                accepted_harvesters = {'default', 'harvest'}
                if user_name in accepted_harvesters:
                    pkg_dict['source'] = 'External'
                else:
                    pkg_dict['source'] = 'Internal'

        vocab_fields = ['international_benchmarks', 'geographical_coverage', 'high_value_dataset_category']
        for field in vocab_fields:
            if pkg_dict.get(field):
                pkg_dict['vocab_%s' % field] = [tag for tag in json.loads(pkg_dict[field])]

        # Map keywords to vocab_keywords_{lang}
        translated_vocabs = ['keywords', 'content_type', 'update_frequency']
        languages = ['fi', 'sv', 'en']
        ignored_tags = ["avoindata.fi"]
        for prop_key in translated_vocabs:
            prop_json = pkg_dict.get(prop_key)
            # Add only if not already there
            if not prop_json:
                continue
            prop_value = json.loads(prop_json)
            # Add for each language
            for lang in languages:
                if isinstance(prop_value, dict) and prop_value.get(lang):
                    prop_value[lang] = [tag for tag in {tag.lower() for tag in prop_value[lang]} if tag not in ignored_tags]
                    pkg_dict['vocab_%s_%s' % (prop_key, lang)] = [tag for tag in prop_value[lang]]
            pkg_dict[prop_key] = json.dumps(prop_value)

        if 'date_released' in pkg_dict and ISO_DATETIME_FORMAT.match(pkg_dict['date_released']):
            pkg_dict['metadata_created'] = "%sZ" % pkg_dict['date_released']

        if pkg_dict.get('organization', None) is not None:
            org = toolkit.get_action('organization_show')({}, {'id': pkg_dict.get('organization')})
            if 'producer_type' in org:
                pkg_dict['producer_type'] = org['producer_type']

        if pkg_dict.get('highvalue_category'):
            pkg_dict['vocab_highvalue_category'] = json.loads(pkg_dict.get('highvalue_category'))

        return pkg_dict

    def before_view(self, pkg_dict):
        # remove unwanted keywords from being passed to the view
        languages = ['fi', 'sv', 'en']
        ignored_tags = ["avoindata.fi"]
        keywords = pkg_dict.get('keywords')
        for lang in languages:
            if keywords and keywords.get(lang):
                keywords[lang] = [tag for tag in {tag.lower() for tag in keywords[lang]} if tag not in ignored_tags]

        return pkg_dict

    def after_search(self, search_results, search_params):
        # Modify facet display name to be human-readable
        # TODO: handle translations for groups and highvalue categories
        if search_results.get('search_facets'):
            highvalue_facet = search_results['search_facets'].get('vocab_highvalue_category')
            if highvalue_facet:
                for facet_item in highvalue_facet['items']:
                    facet_item['display_name'] = get_highvalue_category_label(facet_item['name'])

        return search_results

    # IActions #
    def get_actions(self):
        return {'package_show': action_package_show, 'package_search': action_package_search,
                'package_autocomplete': package_autocomplete, 'store_municipality_bbox_data': store_municipality_bbox_data,
                'dcat_catalog_show': dcat_catalog_show,
                'statistics': statistics}

    # IValidators
    def get_validators(self):
        return {
            'check_deprecation': validators.check_deprecation,
            'convert_to_list': validators.convert_to_list,
            'lowercase': validators.lowercase,
            'create_fluent_tags': validators.create_fluent_tags,
            'create_tags': validators.create_tags,
            'from_date_is_before_until_date': validators.from_date_is_before_until_date,
            'ignore_if_invalid_isodatetime': validators.ignore_if_invalid_isodatetime,
            'keep_old_value_if_missing': validators.keep_old_value_if_missing,
            'list_to_string': validators.list_to_string,
            'string_to_list': validators.string_to_list,
            'lower_if_exists': validators.lower_if_exists,
            'only_default_lang_required': validators.only_default_lang_required,
            'override_field_with_default_translation': validators.override_field_with_default_translation,
            'override_field': validators.override_field,
            'repeating_text_output': validators.repeating_text_output,
            'repeating_text': validators.repeating_text,
            'repeating_email': validators.repeating_email,
            'repeating_url': validators.repeating_url,
            'set_private_if_not_admin_or_showcase_admin': validators.set_private_if_not_admin_or_showcase_admin,
            'tag_list_output': validators.tag_list_output,
            'tag_string_or_tags_required': validators.tag_string_or_tags_required,
            'upper_if_exists': validators.upper_if_exists,
            'admin_only_field': validators.admin_only_field,
            'use_url_for_name_if_left_empty': validators.use_url_for_name_if_left_empty,
            'convert_to_json_compatible_str_if_str': validators.convert_to_json_compatible_str_if_str,
            'empty_string_if_value_missing': validators.empty_string_if_value_missing,
            'resource_url_validator': validators.resource_url_validator,
            'highvalue_category': validators.highvalue_category
        }

    def get_blueprint(self):
        return views.get_blueprint()



class YTPSpatialHarvester(plugins.SingletonPlugin):
    try:
        from ckanext.spatial.interfaces import ISpatialHarvester
        plugins.implements(ISpatialHarvester, inherit=True)
    except ImportError:
        pass

    # ISpatialHarvester

    def get_package_dict(self, context, data_dict):

        context['defer'] = True
        package_dict = data_dict['package_dict']

        list_map = {'access_constraints': 'copyright_notice'}

        for source, target in list_map.items():
            for extra in package_dict['extras']:
                if extra['key'] == source:
                    value = json.loads(extra['value'])
                    if len(value):
                        package_dict['extras'].append({
                            'key': target,
                            'value': value[0]
                        })

        value_map = {'contact-email': ['maintainer_email']}

        for source, target in value_map.items():
            for extra in package_dict['extras']:
                if extra['key'] == source and len(extra['value']):
                    for target_key in target:
                        # some have multiple emails separated by ;
                        package_dict[target_key] = [email.strip() for email in extra['value'].split(";")]

        map = {'responsible-party': ['maintainer']}

        harvester_context = {'model': model, 'session': Session, 'user': 'harvest'}
        for source, target in map.items():
            for extra in package_dict['extras']:
                if extra['key'] == source:
                    value = json.loads(extra['value'])
                    if len(value):
                        for target_key in target:
                            package_dict[target_key] = value[0]['name']

                        # find responsible party from orgs
                        try:
                            name = munge_title_to_name(value[0]['name'])
                            group = get_action('organization_show')(harvester_context, {'id': name,
                                                                                        'include_users': False,
                                                                                        'include_dataset_count': False,
                                                                                        'include_groups': False,
                                                                                        'include_tags': False,
                                                                                        'include_followers': False})
                            if group['state'] == 'active':
                                package_dict['owner_org'] = group['id']
                        except NotFound:
                            pass

        # If maintainer was not mapped from responsible organization, lets use individual name instead
        if not package_dict.get('maintainer') and data_dict.get('iso_values', {}).get('metadata-point-of-contact'):
            point_of_contacts = data_dict['iso_values']['metadata-point-of-contact']
            for contact in point_of_contacts:
                if contact.get('individual-name'):
                    package_dict['maintainer'] = contact.get('individual-name')
                    break

        config_obj = json.loads(data_dict['harvest_object'].source.config or "{}")
        license_from_source = config_obj.get("license", None)
        if license_from_source is not None:
            package_dict['license_id'] = license_from_source

        licenses = get_action('license_list')(context, {})
        extras = {extra['key']: extra['value'] for extra in package_dict['extras']}

        # If license wasn't found from source, try to figure it out from url:s
        if license_from_source is None:
            license_id = 'notspecified'
            license_value = json.loads(extras.get('licence', '[]'))
            access_constraints_value = json.loads(extras.get('access_constraints', '[]'))

            if len(license_value) > 0:
                license_obj = license_value
                url_pattern = re.compile(r'(https?://\S+[^.,) ])')
                urls = [url for v in license_value for url in url_pattern.findall(v)]

                if urls:
                    license_id = 'other'
                    http_urls = {re.sub('^https', 'http', url) for url in urls}
                    matching_license = next((li for li in licenses if li.get('url') in http_urls), None)
                    if matching_license is not None:
                        license_id = matching_license['id']
                        license_obj = matching_license
                    else:
                        package_dict['extras'].append({
                            "key": 'license_url',
                            'value': urls[0]
                        })

                package_dict['license_id'] = license_id
                package_dict['license'] = license_obj

            if len(access_constraints_value) > 0 and license_id in ['other', 'notspecified']:
                license_obj = access_constraints_value
                url_pattern = re.compile(r'(https?://\S+[^.,) ])')
                urls = [url for v in access_constraints_value for url in url_pattern.findall(v)]

                if urls:
                    license_id = 'other'
                    http_urls = {re.sub('^https', 'http', url) for url in urls}
                    matching_license = next((li for li in licenses if li.get('url') in http_urls), None)
                    if matching_license is not None:
                        license_id = matching_license['id']
                        license_obj = matching_license
                    else:
                        package_dict['extras'].append({
                            "key": 'license_url',
                            'value': urls[0]
                        })

                package_dict['license_id'] = license_id
                package_dict['license'] = license_obj

            if package_dict.get('license_id', None) is None:
                package_dict['license_id'] = license_id


        # Get the license url links
        iso_values = data_dict.get('iso_values')
        license_links = iso_values.get('other-constraints', None)

        # if any licence links were found, map them to one of the existing licences
        # licences that don't fall under cc-by-4.0 or cc-zero-1.0 will not be harvested
        if license_links:

            # Mappings for the license urls
            valid_licenses = {
                "https://creativecommons.org/licenses/by/4.0/": "cc-by-4.0",
                "https://creativecommons.org/publicdomain/zero/1.0/deed.fi": "cc-zero-1.0"
            }

            for license_link in license_links:
                if license_link in valid_licenses.keys():
                    # if the licence was found, assign the value to the licence_id field
                    package_dict['license_id'] = valid_licenses[license_link]
                    package_dict['license_url'] = license_link

        # if the license is not open enough, do not harvest the resource
        harvested_licences = ['cc-by-4.0', 'cc-zero-1.0']
        if package_dict.get('license_id', "") not in harvested_licences:
            logging.info(f"Skipping harvesting {package_dict.get('title', '')} as its license "
                         f"[{package_dict.get('license_id', '')}] was not in the list of accepted licenses")
            return


        if extras.get('temporal-extent-begin', None) is not None:
            try:
                value = iso8601.parse_date(extras['temporal-extent-begin'])
                package_dict['valid_from'] = value
            except iso8601.ParseError:
                log.info("Could not convert %s to datetime" % extras['temporal-extent-begin'])

        if extras.get('temporal-extent-end', None) is not None:
            try:
                value = iso8601.parse_date(extras['temporal-extent-end'])
                package_dict['valid_till'] = value
            except iso8601.ParseError:
                log.info("Could not convert %s to datetime" % extras['temporal-extent-end'])

        if extras.get('dataset-reference-date', None) is not None:
            creation_date = None
            publication_date = None
            try:
                value_list = json.loads(extras['dataset-reference-date'])
                for value in value_list:
                    if value.get('type') == "creation":
                        creation_date = iso8601.parse_date(value.get('value'))\
                                    .replace(tzinfo=None).isoformat()
                    elif value.get('type') == 'publication':
                        publication_date = iso8601.parse_date(value.get('value'))\
                                    .replace(tzinfo=None).isoformat()

                if creation_date:
                    package_dict['date_released'] = creation_date
                elif publication_date:
                    package_dict['date_released'] = publication_date
            except json.JSONDecodeError:
                pass

        # TODO: Move to dataset level
        if extras.get('spatial-reference-system', None) is not None:
            for resource in package_dict.get('resources', []):
                resource['position_info'] = extras['spatial-reference-system']

        # Map topic-categories to categories
        iso_values = data_dict.get('iso_values')
        if iso_values.get('topic-category', None) is not None:
            topic_categories = iso_values.get('topic-category')
            categories = [category for topic_category in topic_categories
                          for category, iso_topic_categories in six.iteritems(_category_mapping)
                          if topic_category in iso_topic_categories]
            package_dict['categories'] = categories
            package_dict['extras'].append({'key': 'topic-category', 'value': topic_categories})

        package_dict['keywords'] = {'fi': []}


        # Map tags to keywords
        tags = package_dict.get('tags')

        for tag in tags:
            try:
                tag_name_validator(tag.get('name'), context)
                tag_length_validator(tag.get('name'), context)
                package_dict['keywords']['fi'].append(tag.get('name'))
            except Invalid:
                log.info("Invalid tag found %s, skipping..", tag.get('name'))
                pass

        # Remove tags
        package_dict.pop('tags')

        package_dict['notes_translated'] = {"fi": package_dict['notes']}
        package_dict['title_translated'] = {"fi": package_dict['title']}
        package_dict['collection_type'] = 'Open Data'


        # Apiset mapping (resource-type 'services' are mapped to apisets)
        res_type = iso_values.get('resource-type', None)

        # res_type is in the form ['dataset', ...], usually containing one or more resource types
        if 'service' in res_type:
            package_dict['type'] = 'apiset'
            package_dict['api_provider'] = package_dict.get('maintainer', None)
            # maintainer email is provided as an array
            if package_dict.get('maintainer_email', None):
                package_dict['api_provider_email'] = package_dict['maintainer_email'][0]

            # remove maintainer and maintainer_email or they will cause validation error for apisets
            package_dict.pop('maintainer', None)
            package_dict.pop('maintainer_email', None)


            # get all resources from the apiset
            apiset_resources = package_dict.get('resources', [])
            for apiset_resource in apiset_resources:
                # get the format and map it into formats field
                apiset_resource['formats'] = apiset_resource.get('format', None)

            # update the resources for the apiset
            package_dict['resources'] = apiset_resources

        return package_dict


# Adds new users to every group
@chained_action
def action_user_create(original_action, context, data_dict):
    result = original_action(context, data_dict)

    if result:
        context = create_system_context()

        groups = plugins.toolkit.get_action('group_list')(context, {})

        for group in groups:
            member_data = {'id': group, 'username': result['name'], 'role': 'editor'}
            plugins.toolkit.get_action('group_member_create')(context, member_data)

    return result


# Adds all users to newly created groups
@chained_action
def action_group_create(original_action, context, data_dict):
    result = original_action(context, data_dict)

    if result and data_dict.get('type', 'group') == 'group':
        context = create_system_context()

        users = plugins.toolkit.get_action('user_list')(context, {})

        for user in users:
            member_data = {'id': result['id'], 'username': user['name'], 'role': 'editor'}
            plugins.toolkit.get_action('group_member_create')(context, member_data)

    return result


@logic.side_effect_free
def action_organization_tree_list(context, data_dict):
    check_access('site_read', context)
    check_access('group_list', context)

    q = data_dict.get('q', '')
    sort_by = data_dict.get('sort_by', 'name asc')
    page = toolkit.asint(data_dict.get('page', 1))
    items_per_page = toolkit.asint(data_dict.get('items_per_page', 21))
    with_datasets = toolkit.asbool(data_dict.get('with_datasets', False))
    user = context.get('user')

    # Determine non-visible organizations
    if context.get('user_is_sysadmin', False):
        non_approved = []
    else:
        # Find names of all non-approved organizations
        query = (model.Session.query(model.Group.name)
                 .filter(model.Group.state == 'active')
                 .filter(model.Group.approval_status != 'approved'))

        non_approved = set(result[0] for result in query.all())

        # If user is logged in, retain only names of organizations the user is not a member of
        if user:
            query = (model.Session.query(model.Group.name)
                     .join(model.Member, model.Member.group_id == model.Group.id)
                     .join(model.User, model.User.id == model.Member.table_id)
                     .filter(model.Member.state == 'active')
                     .filter(model.Member.table_name == 'user')
                     .filter(model.User.name == user)
                     .filter(model.Group.state == 'active')
                     .filter(model.Group.approval_status != 'approved'))
            memberships = set(result[0] for result in query.all())
            non_approved -= memberships

    parent_member = sqlalchemy.orm.aliased(model.Member)
    parent_group = sqlalchemy.orm.aliased(model.Group)
    parent_extra = sqlalchemy.orm.aliased(model.GroupExtra)
    child_member = sqlalchemy.orm.aliased(model.Member)
    child_group = sqlalchemy.orm.aliased(model.Group)

    # Fetch ids of all visible organizations filtered in maybe correct order
    ids_and_titles = (model.Session.query(model.Group.id, model.Group.title, model.GroupExtra.value)
                      .filter(model.Group.state == 'active')
                      .filter(model.Group.is_organization.is_(True))
                      .filter(model.Group.name.notin_(non_approved))
                      .outerjoin(model.GroupExtra, and_(model.GroupExtra.group_id == model.Group.id,
                                                        model.GroupExtra.key == 'title_translated'))
                      .order_by(model.Group.title))

    # Optionally handle getting only organizations with datasets
    # Note! Check if state is deleted for the results or else it will return all
    # dataset collections that have had a dataset at some point
    if with_datasets:
        ids_and_titles = (
                ids_and_titles
                .outerjoin(model.Package, and_(model.Package.type == 'dataset',
                                               model.Package.private == false(),
                                               model.Package.state == 'active',
                                               or_(model.Package.owner_org == model.Group.name,
                                                   model.Package.owner_org == model.Group.id)))
                .group_by(model.Group.id, model.Group.title, model.GroupExtra.value)
                .having(sqlalchemy.func.count(model.Package.id) > 0))

    ids_and_titles = list(ids_and_titles.all())

    # Pick translated title for each result
    lang = helpers.lang() or config.get('ckan.locale_default', 'en')

    def translated_or_title(translated, title):
        if translated is not None:
            return json.loads(translated)
        else:
            return {lang: title}

    translated_titles_and_gids = ((translated_or_title(translated, title).get(lang, title).lower(), gid)
                                  for gid, title, translated in ids_and_titles)

    # Filter based on search query if provided
    if q:
        result_titles_and_gids = ((title, gid) for title, gid in translated_titles_and_gids
                                  if q.lower() in title)
    else:
        result_titles_and_gids = translated_titles_and_gids

    # Sort global results correctly into a list of ids
    if sort_by == 'name desc':
        sorted_titles_and_gids = sorted(result_titles_and_gids, reverse=True)
    else:
        sorted_titles_and_gids = sorted(result_titles_and_gids)

    global_results = [gid for title, gid in sorted_titles_and_gids]

    # Early return for empty results
    if not global_results:
        return {'global_results': [], 'page_results': []}

    # Slice current page ids
    page_ids = global_results[(page - 1) * items_per_page:page * items_per_page]

    # Fetch details for organizations on current page
    page_orgs = (
            model.Session.query(model.Group.id, model.Group.name, model.Group.title,
                                model.GroupExtra.value, sqlalchemy.func.count(sqlalchemy.distinct(model.Package.id)),
                                parent_group.name, parent_group.title, parent_extra.value,
                                sqlalchemy.func.count(sqlalchemy.distinct(child_group.id)))
            .outerjoin(model.GroupExtra, and_(model.GroupExtra.group_id == model.Group.id,
                                              model.GroupExtra.key == 'title_translated',
                                              model.GroupExtra.state == 'active'))
            .outerjoin(model.Package, and_(model.Package.type == 'dataset',
                                           model.Package.private == false(),
                                           model.Package.state == 'active',
                                           or_(model.Package.owner_org == model.Group.name,
                                               model.Package.owner_org == model.Group.id)))
            .outerjoin(parent_member, and_(parent_member.group_id == model.Group.id,
                                           parent_member.table_name == 'group'))
            .outerjoin(parent_group, parent_group.id == parent_member.table_id)
            .outerjoin(parent_extra, and_(parent_extra.group_id == parent_group.id,
                                          parent_extra.key == 'title_translated'))
            .outerjoin(child_member, and_(child_member.table_id == model.Group.id,
                                          child_member.table_name == 'group'))
            .outerjoin(child_group, child_group.id == child_member.group_id)
            .filter(model.Group.id.in_(page_ids))
            .group_by(model.Group.id, model.Group.name,
                      model.Group.title, model.GroupExtra.value,
                      parent_group.name, parent_group.title, parent_extra.value)
            .all())

    page_results_by_id = {gid: {
        'id': name, 'title': title, 'title_translated': translated_or_title(title_translated, title),
        'package_count': package_count, 'parent_name': parent_name,
        'parent_title': parent_title, 'parent_title_translated': parent_title_translated,
        'child_count': child_count
        } for gid, name, title, title_translated, package_count,
        parent_name, parent_title, parent_title_translated, child_count in page_orgs}

    # Retain global sorting
    page_results = [page_results_by_id[gid] for gid in page_ids]

    return {'global_results': global_results,
            'page_results': page_results}


class YtpOrganizationsPlugin(plugins.SingletonPlugin, DefaultOrganizationForm, YtpMainTranslation):
    """ CKAN plugin to change how organizations work """
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(ISiteSearch, inherit=True)

    # IConfigurer
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')

    _localized_fields = ['title', 'description', 'alternative_name', 'street_address', 'street_address_pobox',
                         'street_address_zip_code', 'street_address_place_of_business', 'street_address_country',
                         'street_address_unofficial_name', 'street_address_building_id', 'street_address_getting_there',
                         'street_address_parking', 'street_address_public_transport', 'street_address_url_public_transport',
                         'homepage']

    def get_auth_functions(self):
        return {'organization_create': auth.organization_create}

    def get_actions(self):
        return {'user_create': action_user_create,
                'group_create': action_group_create,
                'organization_tree_list': action_organization_tree_list,
                'group_tree': plugin_hierarchy.group_tree,
                'group_tree_section': plugin_hierarchy.group_tree_section,
                }

    def get_blueprint(self):
        '''Return a Flask Blueprint object to be registered by the app.'''

        return views_organization.get_blueprints()

    # IValidators
    def get_validators(self):
        return {
            "is_admin_in_parent_if_changed": validators.is_admin_in_parent_if_changed,
            "is_allowed_parent": validators.is_allowed_parent,
            'keep_old_organization_value_if_missing': validators.keep_old_organization_value_if_missing,
            'get_removed_checkbox_extra': validators.get_removed_checkbox_extra,
            "extra_validators_multiple_choice": validators.extra_validators_multiple_choice,
            'admin_only_feature': validators.admin_only_feature
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "get_last_harvested_date": get_last_harvested_date,
            "group_tree_section": group_tree_section
        }

    # ISiteSearch
    def after_organization_search(self, results, data_dict):
        without_unapproved = [r for r in results.get('results', [])
                              if r.get('approval_status') == 'approved']
        results['results'] = without_unapproved
        results['count'] = len(without_unapproved)
        return results


class YtpReportPlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(IReport)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITranslation)

    # IReport

    def register_reports(self):
        from . import reports
        return [
            reports.administrative_branch_summary_report_info,
            reports.deprecated_datasets_report_info,
        ]

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')


class YtpThemePlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)

    default_domain = None
    logos = {}

    # TODO: We should use named routes instead
    _menu_map = [
                    (
                        [
                            '/user/%(username)s',
                            '/%(language)s/user/%(username)s'
                        ],
                        menu.UserMenu,
                        menu.MyInformationMenu
                    ),
                    (
                        [
                            '/dashboard',
                            '/dashboard/',
                            '/%(language)s/dashboard',
                            '/%(language)s/dashboard/'
                        ],
                        menu.UserMenu,
                        menu.MyDashboardMenu
                    ),
                    (
                        [
                            '/dashboard/organizations',
                            '/%(language)s/dashboard/organizations'
                        ],
                        menu.UserMenu,
                        menu.MyOrganizationMenu,
                    ),
                    (
                        [
                            '/dashboard/datasets',
                            '/%(language)s/dashboard/datasets'
                        ],
                        menu.UserMenu,
                        menu.MyDatasetsMenu
                    ),
                    (
                        [
                            '/user/delete-me',
                            '/%(language)s/user/delete-me'
                        ],
                        menu.UserMenu,
                        menu.MyCancelMenu
                    ),
                    (
                        [
                            '/user/edit',
                            '/%(language)s/user/edit',
                            '/user/edit/%(username)s',
                            '/%(language)s/user/edit/%(username)s'
                        ],
                        menu.UserMenu,
                        menu.MyPersonalDataMenu,
                    ),
                    (
                        [
                            '/user/activity/%(username)s',
                            '/%(language)s/user/activity/%(username)s'
                        ],
                        menu.UserMenu,
                        menu.MyInformationMenu
                    ),
                    (
                        [
                            '/user',
                            '/%(language)s/user'
                        ],
                        menu.ProducersMenu,
                        menu.ListUsersMenu
                    ),
                    (
                        [
                            '/%(language)s/organization',
                            '/organization'
                        ],
                        menu.EmptyMenu,
                        menu.OrganizationMenu
                    ),
                    (
                        [
                            '/%(language)s/dataset/new?collection_type=Open+Data',
                            '/dataset/new?collection_type=Open+Data'
                        ],
                        menu.PublishMenu,
                        menu.PublishDataMenu
                    ),
                    (
                        [
                            '/%(language)s/dataset/new?collection_type=Interoperability+Tools',
                            '/dataset/new?collection_type=Interoperability+Tools'
                        ],
                        menu.PublishMenu,
                        menu.PublishToolsMenu
                    ),
                    (
                        [
                            '/%(language)s/service/new',
                            '/service/new'
                        ],
                        menu.PublishMenu,
                        menu.PublishServiceMenu
                    ),
                    (
                        [
                            '/%(language)s/postit/return',
                            '/postit/return'
                        ],
                        menu.ProducersMenu,
                        menu.PostitNewMenu
                    ),
                    (
                        [
                            '/%(language)s/postit/new',
                            '/postit/new'
                        ],
                        menu.ProducersMenu,
                        menu.PostitNewMenu
                    )
                ]

    # IRoutes #

    def before_map(self, m):
        """ Redirect data-path in stand-alone environment directly to CKAN. """
        m.redirect('/data/*(url)', '/{url}', _redirect_code='301 Moved Permanently')

        controller = 'ckanext.ytp.controller:YtpThemeController'
        m.connect('/postit/new', controller=controller, action='new_template')
        m.connect('/postit/return', controller=controller, action='return_template')

        return m

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, 'resources/templates')
        toolkit.add_resource('resources', 'ytp_resources')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_template_directory(config, 'postit')

    # IConfigurable #

    def configure(self, config):
        self.default_domain = config.get("ckanext.ytp.default_domain")
        logos = config.get("ckanext.ytp.theme.logos")
        if logos:
            self.logos = dict(item.split(":") for item in re.split("\\s+", logos.strip()))

    # ITemplateHelpers #

    def _short_domain(self, hostname, default=None):
        if not hostname or hostname[0].isdigit():
            return default or self.default_domain or ""
        return '.'.join(hostname.split('.')[-2:])

    def _get_menu_tree(self, current_url, language):
        parsed_url = urllib.parse.urlparse(current_url)
        for patterns, handler, selected in self._menu_map:
            for pattern in patterns:
                if type(pattern) in (str,):
                    values = {'language': language}
                    if c.user:
                        values['username'] = c.user
                    try:
                        pattern_url = urllib.parse.urlparse(pattern % values)

                        if parsed_url.path == pattern_url.path:
                            skip = False
                            if pattern_url.query:
                                parsed_parameters = urllib.parse.parse_qs(parsed_url.query)
                                if not parsed_parameters:
                                    skip = True
                                else:
                                    for key, value in urllib.parse.parse_qs(pattern_url.query).items():
                                        parameter = parsed_parameters.get(key, None)
                                        if not parameter or parameter[0] != value[0]:
                                            skip = True
                                            break
                            if not skip:
                                return handler(self).select(selected).to_drupal_dictionary()
                    except KeyError:
                        pass  # user not logged in
                elif pattern.match(current_url):
                    return handler(self).select(selected).to_drupal_dictionary()
        return None

    def _get_menu_for_page(self, current_url, language):
        """ Fetches static side menu for url and language. """
        tree = self._get_menu_tree(current_url, language)
        if tree:
            return {'tree': tree}
        else:
            return {}

    def _drupal_snippet(self, path):
        lang = get_lang_prefix()
        import requests
        import hashlib

        try:
            # Call our custom Drupal API to get drupal block content
            hostname = config.get('ckanext.drupal8.site_url')
            domains = config.get('ckanext.drupal8.domain').split(",")
            verify_cert = config.get('ckanext.drupal8.development_cert', '') or True
            cookies = {}
            for domain in domains:
                # Split domain from : and expect first part to be hostname and second part be port.
                # Here we ignore the port as drupal seems to ignore the port when generating cookiename hashes
                domain_hash = hashlib.sha256(domain.split(':')[0].encode('utf-8')).hexdigest()[:32]
                cookienames = (template % domain_hash for template in ('SESS%s', 'SSESS%s'))
                named_cookies = ((name, p.toolkit.request.cookies.get(name)) for name in cookienames)
                for cookiename, cookie in named_cookies:
                    if cookie is not None:
                        cookies.update({cookiename: cookie})

            # If user hasn't signed in, no need to fetch non-cached content
            if cookies == {}:
                hostname = config.get('ckanext.drupal8.site_url_internal')
            snippet_url = '%s/%s/%s' % (hostname, lang, path)

            host = config.get('ckanext.drupal8.domain', '').split(',', 1)[0]
            headers = {'Host': host}
            response = requests.get(snippet_url, cookies=cookies, verify=verify_cert, headers=headers)
            return response.text
        except requests.exceptions.RequestException as e:
            log.error('%s' % e)
            return ''
        except Exception as e:
            log.error('%s' % e)
            return ''

        return None

    def _drupal_footer(self):
        return self._drupal_snippet('api/footer')

    def _drupal_header(self):
        # Path variable depends on request type
        path = request.full_path if is_flask_request() else request.path_qs
        result = self._drupal_snippet('api/header?activePath=%s' % path)
        if result:
            # Language switcher links will point to /api/header, fix them based on currently requested page
            result = re.sub('\\?activePath=/(\\w+)', '', result)
            return re.sub('href="/(\\w+)/api/header([^\"]+)*"', 'href="/data/\\1%s"' % path, result)
        return result

    def get_helpers(self):
        return {'short_domain': self._short_domain, 'get_menu_for_page': self._get_menu_for_page,
                'drupal_footer': self._drupal_footer, 'drupal_header': self._drupal_header}


def helper_linked_user(user, maxlength=0, avatar=20):
    """ Return user as HTML item """
    if isinstance(user, dict):
        user_id = user['id']
        user_name = user['name']
        user_displayname = user['display_name']
    elif isinstance(user, model.User):
        user_id = user.id
        user_name = user.name
        user_displayname = user.display_name
    else:
        user_obj = model.User.get(six.text_type(user))
        if not user_obj:
            return user
        else:
            user_id = user_obj.id
            user_name = user_obj.name
            user_displayname = user_obj.display_name

    if not model.User.VALID_NAME.match(user_name):
        user_name = user_id

    if maxlength and len(user_displayname) > maxlength:
        user_displayname = user_displayname[:maxlength] + '...'
    return helpers.link_to(user_displayname, helpers.url_for(controller='user', action='read', id=user_name), class_='')


class YtpUserPlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)

    default_domain = None

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def configure(self, config):
        pass

    def get_helpers(self):
        return {'linked_user': helper_linked_user}

    def get_auth_functions(self):
        return {'user_update': plugin_logic.auth_user_update,
                'user_list': plugin_logic.auth_user_list,
                'admin_list': plugin_logic.auth_admin_list}


class YtpRestrictCategoryCreationAndUpdatingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthFunctions)

    def admin_only_for_categories(self, context, data_dict=None):
        return {'success': False, 'msg': 'Only admins can create and edit new categories'}

    def get_auth_functions(self):
        return {'group_create': self.admin_only_for_categories,
                'group_update': self.admin_only_for_categories}


class YtpIPermissionLabelsPlugin(
        plugins.SingletonPlugin, DefaultPermissionLabels):
    '''
    Permission labels for controlling permissions of different user roles
    '''
    plugins.implements(plugins.IPermissionLabels)

    def get_dataset_labels(self, dataset_obj):
        '''
        Showcases get showcase-admin label so that showcase admins have
        rights for that showcase
        '''
        # Default labels
        labels = super(YtpIPermissionLabelsPlugin, self).get_dataset_labels(dataset_obj)

        if dataset_obj.type == "showcase":
            labels.append('showcase-admin')

        return labels

    def get_user_dataset_labels(self, user_obj):
        '''
        Showcase admin users get a showcase-admin label
        '''
        # Default labels
        labels = super(YtpIPermissionLabelsPlugin, self).get_user_dataset_labels(user_obj)

        if user_obj and ShowcaseAdmin.is_user_showcase_admin(user_obj):
            labels.append('showcase-admin')

        return labels


class OpenDataGroupPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.interfaces.IActions)

    def get_actions(self):
        return {
            "group_create": self._group_create
        }

    @chained_action
    def _group_create(self, original_action, context, data_dict):
        auth_context = {'ignore_auth': True}
        users = get_action('user_list')(auth_context, {})

        data_dicts = []
        for user in users:
            data_dicts.append({'name': user['name'], 'capacity': 'editor'})

        data_dict['users'] = data_dicts
        return original_action(context, data_dict)


# NOTE: DO NOT ENABLE THIS PLUGIN IN NON-LOCAL ENVIRONMENTS
class OpenDataResetPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.interfaces.IActions)

    def get_actions(self):
        return {
            "reset": _reset
        }
@toolkit.side_effect_free
def _reset(context, data_dict):

    context = {'ignore_auth': True}

    # clean database
    from ckan import model
    model.repo.delete_all()


    # clear search index
    from ckan.lib.search import clear_all
    clear_all()

    # sparql clear
    get_action('sparql_clear')(context, {})

    # Create platform vocabulary

    vocab_id = 'platform'
    tags = (u"Android", u"iOS Apple", u"Windows", u"Mac OS X", u"Website", u"Other")
    tags_to_delete = []
    tags_to_create = []
    try:
        data = {'id': vocab_id}
        old_tags = toolkit.get_action('vocabulary_show')(context, data)
        for old_tag in old_tags.get('tags'):
            if old_tag['id'] in tags:
                continue
            else:
                tags_to_delete.append({'name': old_tag['name']})
                toolkit.get_action('tag_delete')(context, {'id': old_tag['id']})

        for tag in tags:
            try:
                toolkit.get_action('tag_show')(context, {'id': tag, 'vocabulary_id': vocab_id})
            except toolkit.ObjectNotFound:
                tags_to_create.append({'name': tag})
                toolkit.get_action('tag_create')(context, {'name': tag, 'vocabulary_id': old_tags.get('id')})
    except NotFound:
        data = {'name': vocab_id}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tags_to_create.append({'name': tag})
            toolkit.get_action('tag_create')(context, data)

    return "Cleared"
