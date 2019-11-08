import json
import logging
import pylons
import re
import types
import urlparse
import validators

import ckan.lib.base as base
import logic as plugin_logic
import ckan.plugins as p
from ckan import authz as authz

from ckan import plugins, model, logic
from ckan.common import _, c, request, is_flask_request

from ckan.config.routing import SubMapper
from ckan.lib import helpers
from ckan.lib.munge import munge_title_to_name
from ckan.lib.navl.dictization_functions import Missing, flatten_dict, unflatten, Invalid
from ckan.lib.plugins import DefaultOrganizationForm, DefaultTranslation, DefaultPermissionLabels
from ckan.logic import NotFound, NotAuthorized, get_action
from ckan.model import Session
from ckan.plugins import toolkit
from ckan.plugins.toolkit import config, chained_action
from ckanext.report.interfaces import IReport
from ckanext.spatial.interfaces import ISpatialHarvester
from ckanext.showcase.model import ShowcaseAdmin
from paste.deploy.converters import asbool
from webhelpers.html import escape
from webhelpers.html.tags import link_to

import auth
import menu

from converters import convert_to_tags_string, save_to_groups

from helpers import extra_translation, render_date, service_database_enabled, get_json_value, \
    sort_datasets_by_state_priority, get_facet_item_count, get_remaining_facet_item_count, sort_facet_items_by_name, \
    get_sorted_facet_items_dict, calculate_dataset_stars, get_upload_size, get_license, get_visits_for_resource, \
    get_visits_for_dataset, get_geonetwork_link, calculate_metadata_stars, get_tooltip_content_types, unquote_url, \
    sort_facet_items_by_count, scheming_field_only_default_required, add_locale_to_source, scheming_language_text_or_empty, \
    get_lang_prefix, call_toolkit_function, get_translated, dataset_display_name, resource_display_name, \
    get_visits_count_for_dataset_during_last_year, get_current_date, get_download_count_for_dataset_during_last_year, \
    get_label_for_producer, scheming_category_list, check_group_selected, group_title_by_id, group_list_with_selected, \
    get_last_harvested_date, get_resource_sha256

from tools import create_system_context, get_original_method

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


class YtpMainTranslation(DefaultTranslation):

    def i18n_domain(self):
        return "ckanext-ytp_main"


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
    except Exception, e:
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
    return escape(unicode(value))


def _prettify(field_name):
    """ Taken from ckan.logic.ValidationError.error_summary """
    field_name = re.sub('(?<!\\w)[Uu]rl(?!\\w)', 'URL', field_name.replace('_', ' ').capitalize())
    return _(field_name.replace('_', ' '))


def _format_value(value):
    if isinstance(value, types.DictionaryType):
        value_buffer = []
        for key, item_value in value.iteritems():
            value_buffer.append(_dict_formatter(key, item_value))
        return value_buffer
    elif isinstance(value, types.ListType):
        value_buffer = []
        for item_value in value:
            value_buffer.append(_format_value(item_value))
        return value_buffer

    return _escape(value)


def _format_extras(extras):

    if not extras:
        return ""
    extra_buffer = {}
    for extra_key, extra_value in extras.iteritems():
        extra_buffer.update(_dict_formatter(extra_key, extra_value))
    return extra_buffer


def _dict_formatter(key, value):
    value_formatter = _key_functions.get(key)
    if value_formatter:
        return value_formatter(key, value)
    else:
        value = _format_value(value)
    if key and value:
        return{key: value}
    return {}


def _parse_extras(key, extras):
    extras_dict = dict()
    if not key or not extras:
        log.error("Fail at Extras key: " + repr(key))
        log.error("Fail Extras payload: " + repr(extras))
        return extras_dict
    for extra in extras:
        key = extra.get('key')
        value = extra.get('value')
        extras_dict.update(_dict_formatter(key, value))
    return extras_dict


_key_functions = {u'extras': _parse_extras}


@logic.side_effect_free
def action_package_show(context, data_dict):
    result = get_original_method('ckan.logic.action.get', 'package_show')(context, data_dict)
    organization_data = result.get('organization', None)
    if organization_data:
        organization_id = organization_data.get('id', None)
        if organization_id:
            group = model.Group.get(organization_id)
            result['organization'].update(group.extras)

    return result


@logic.side_effect_free
def action_package_search(context, data_dict):
    data_dict['sort'] = data_dict.get('sort') or 'metadata_created desc'
    return get_original_method('ckan.logic.action.get', 'package_search')(context, data_dict)


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
        self.auto_author = asbool(config.get('ckanext.ytp.auto_author', False))

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
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_resource('public/javascript/', 'ytp_dataset_js')
        toolkit.add_template_directory(config, 'templates')

        toolkit.add_resource('public/javascript/', 'ytp_common_js')
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
        facets_dict.update({'vocab_international_benchmarks': _('International benchmarks')})
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict['vocab_keywords_' + lang] = _('Popular tags')
        facets_dict.update({'vocab_content_type_' + lang: _('Content Type')})
        facets_dict.update({'organization': _('Organization')})
        facets_dict.update({'res_format': _('Formats')})
        # BFW: source is not part of the schema. created artificially at before_index function
        facets_dict.update({'source': _('Source')})
        facets_dict.update({'license_id': _('License')})
        # add more dataset facets here
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        lang = get_lang_prefix()
        facets_dict = OrderedDict()
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict['vocab_keywords_' + lang] = _('Tags')
        facets_dict.update({'vocab_content_type': _('Content Type')})
        facets_dict.update({'res_format': _('Formats')})

        return facets_dict

    # ITemplateHelpers #

    def format_extras(self, extras):
        return _format_extras(extras)

    def _unique_formats(self, resources):
        formats = set()
        for resource in resources:
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
            user_name = unicode(user)
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
                'format_extras': self.format_extras,
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
                'get_visits_for_resource': get_visits_for_resource,
                'get_visits_for_dataset': get_visits_for_dataset,
                'get_visits_count_for_dataset_during_last_year': get_visits_count_for_dataset_during_last_year,
                'get_download_count_for_dataset_during_last_year': get_download_count_for_dataset_during_last_year,
                'get_current_date': get_current_date,
                'get_geonetwork_link': get_geonetwork_link,
                'get_tooltip_content_types': get_tooltip_content_types,
                'unquote_url': unquote_url,
                'scheming_field_only_default_required': scheming_field_only_default_required,
                'add_locale_to_source': add_locale_to_source,
                'scheming_language_text_or_empty': scheming_language_text_or_empty,
                'get_lang_prefix': get_lang_prefix,
                'call_toolkit_function': call_toolkit_function,
                'get_translated': get_translated,
                'dataset_display_name': dataset_display_name,
                'group_title_by_id': group_title_by_id,
                'get_label_for_producer': get_label_for_producer,
                'scheming_category_list': scheming_category_list,
                'check_group_selected': check_group_selected,
                'group_list_with_selected': group_list_with_selected,
                'get_resource_sha256': get_resource_sha256,
                }

    def get_auth_functions(self):
        return {'related_update': auth.related_update,
                'related_create': auth.related_create,
                'package_update': auth.package_update,
                'allowed_to_view_user_list': auth.user_list}

        # IPackageController #

    def after_show(self, context, pkg_dict):
        if u'resources' in pkg_dict and pkg_dict[u'resources']:
            for resource in pkg_dict[u'resources']:
                if 'url_type' in resource and isinstance(resource['url_type'], Missing):
                    resource['url_type'] = None

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
        translated_vocabs = ['keywords', 'content_type']
        languages = ['fi', 'sv', 'en']
        for prop_key in translated_vocabs:
            prop_json = pkg_dict.get(prop_key)
            # Add only if not already there
            if not prop_json:
                continue
            prop_value = json.loads(prop_json)
            # Add for each language
            for lang in languages:
                if prop_value.get(lang):
                    pkg_dict['vocab_%s_%s' % (prop_key, lang)] = [tag for tag in prop_value[lang]]

        if 'date_released' in pkg_dict and ISO_DATETIME_FORMAT.match(pkg_dict['date_released']):
            pkg_dict['metadata_created'] = "%sZ" % pkg_dict['date_released']

        return pkg_dict

    # IActions #
    def get_actions(self):
        return {'package_show': action_package_show, 'package_search': action_package_search}

    # IValidators
    def get_validators(self):
        return {
            'check_deprecation': validators.check_deprecation,
            'convert_to_list': validators.convert_to_list,
            # NOTE: this is a converter. (https://github.com/vrk-kpa/ckanext-scheming/#validators)
            'save_to_groups': save_to_groups,
            'create_fluent_tags': validators.create_fluent_tags,
            'create_tags': validators.create_tags,
            'from_date_is_before_until_date': validators.from_date_is_before_until_date,
            'ignore_if_invalid_isodatetime': validators.ignore_if_invalid_isodatetime,
            'keep_old_value_if_missing': validators.keep_old_value_if_missing,
            'list_to_string': validators.list_to_string,
            'lower_if_exists': validators.lower_if_exists,
            'only_default_lang_required': validators.only_default_lang_required,
            'override_field_with_default_translation': validators.override_field_with_default_translation,
            'override_field': validators.override_field,
            'repeating_text_output': validators.repeating_text_output,
            'repeating_text': validators.repeating_text,
            'set_private_if_not_admin_or_showcase_admin': validators.set_private_if_not_admin_or_showcase_admin,
            'tag_list_output': validators.tag_list_output,
            'tag_string_or_tags_required': validators.tag_string_or_tags_required,
            'upper_if_exists': validators.upper_if_exists,
            'admin_only_field': validators.admin_only_field,
            'use_url_for_name_if_left_empty': validators.use_url_for_name_if_left_empty,
            'convert_to_json_compatible_str_if_str': validators.convert_to_json_compatible_str_if_str
        }


class YTPSpatialHarvester(plugins.SingletonPlugin):
    plugins.implements(ISpatialHarvester, inherit=True)

    # ISpatialHarvester

    def get_package_dict(self, context, data_dict):

        context['defer'] = True
        package_dict = data_dict['package_dict']

        list_map = {'access_constraints': 'copyright_notice'}

        for source, target in list_map.iteritems():
            for extra in package_dict['extras']:
                if extra['key'] == source:
                    value = json.loads(extra['value'])
                    if len(value):
                        package_dict['extras'].append({
                            'key': target,
                            'value': value[0]
                        })

        value_map = {'contact-email': ['maintainer_email', 'author_email']}

        for source, target in value_map.iteritems():
            for extra in package_dict['extras']:
                if extra['key'] == source and len(extra['value']):
                    for target_key in target:
                        package_dict[target_key] = extra['value']

        map = {'responsible-party': ['maintainer', 'author']}

        harvester_context = {'model': model, 'session': Session, 'user': 'harvest'}
        for source, target in map.iteritems():
            for extra in package_dict['extras']:
                if extra['key'] == source:
                    value = json.loads(extra['value'])
                    if len(value):
                        for target_key in target:
                            package_dict[target_key] = value[0]['name']

                        # find responsible party from orgs
                        try:
                            name = munge_title_to_name(value[0]['name'])
                            group = get_action('organization_show')(harvester_context, {'id': name})
                            package_dict['owner_org'] = group['id']
                        except NotFound:
                            pass

        config_obj = json.loads(data_dict['harvest_object'].source.config)
        license_from_source = config_obj.get("license", None)

        for extra in package_dict['extras']:
            if extra['key'] == 'resource-type' and len(extra['value']):
                if extra['value'] == 'dataset':
                    value = 'paikkatietoaineisto'
                    package_dict['collection_type'] = 'Open Data'
                elif extra['value'] == 'series':
                    value = 'paikkatietoaineistosarja'
                    package_dict['collection_type'] = 'Open Data'
                elif extra['value'] == 'service':
                    value = 'paikkatietopalvelu'
                    package_dict['collection_type'] = 'Interoperability Tools'

                else:
                    continue

                package_dict['content_type'] = {"fi": [value]}
                flattened = flatten_dict(package_dict)
                convert_to_tags_string('content_type')(('content_type',), flattened, {}, context)
                package_dict = unflatten(flattened)

            if license_from_source is None:
                if extra['key'] == 'licence':
                    value = json.loads(extra['value'])
                    if len(value):
                        package_dict['license'] = value
                        urls = []
                        for i in value:
                            urls += re.findall(r'(https?://\S+)', i)
                        if len(urls):
                            if urls[0].endswith('.'):
                                urls[0] = urls[0][:-1]
                            package_dict['extras'].append({
                                "key": 'license_url',
                                'value': urls[0]
                            })
                package_dict['license_id'] = 'other'
            else:
                package_dict['license_id'] = license_from_source

            if extra['key'] == 'dataset-reference-date' and len(extra['value']):
                value = json.loads(extra['value'])
                for dates in value:
                    if dates.get("type") == "creation":
                        package_dict['extras'].append({
                            "key": 'resource_created',
                            'value': dates.get("value")
                        })
                    elif dates.get("type") == "publication":
                        package_dict['extras'].append({
                            "key": 'resource_published',
                            'value': dates.get("value")
                        })
                    elif dates.get("type") == "revision":
                        package_dict['extras'].append({
                            "key": 'resource_modified',
                            'value': dates.get("value")
                        })

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

        # topic category for syke

        topic_categories = data_dict['iso_values'].get('topic-category')
        if topic_categories:
            for category in topic_categories:
                category = category[:50] if len(category) > 50 else category
                package_dict['keywords']['fi'].append(category)

        package_dict['notes_translated'] = {"fi": package_dict['notes']}
        package_dict['title_translated'] = {"fi": package_dict['title']}

        return package_dict


_config_template = "ckanext.ytp.%s"
_node_type = 'service_alert'

_default_organization_name = None
_default_organization_title = None


def _get_variable(config, name):
    variable = _config_template % name
    value = config.get(variable)
    if not value:
        raise Exception('YtpOrganizationsPlugin: required configuration variable missing: %s' % (variable))
    return value.decode('unicode_escape')  # CKAN loads ini file as ascii. Parse unicode escapes here.


def _configure(config=None):
    global _default_organization_name, _default_organization_title
    if _default_organization_name and _default_organization_title:
        return
    if not config:
        config = pylons.config
    _default_organization_name = _get_variable(config, "default_organization_name")
    _default_organization_title = _get_variable(config, "default_organization_title")


def _create_default_organization(context, organization_name, organization_title):
    default_locale = config.get('ckan.locale_default', 'fi')
    values = {'name': organization_name,
              'title': organization_title,
              'title_translated': {default_locale: organization_title},
              'id': organization_name}
    try:
        return plugins.toolkit.get_action('organization_show')(context, values)
    except NotFound:
        return plugins.toolkit.get_action('organization_create')(context, values)


# Adds new users to default organization and to every group
def action_user_create(context, data_dict):
    _configure()

    result = get_original_method('ckan.logic.action.create', 'user_create')(context, data_dict)
    context = create_system_context()
    organization = _create_default_organization(context, _default_organization_name, _default_organization_title)
    plugins.toolkit.get_action('organization_member_create')(context, {"id": organization['id'],
                                                                       "username": result['name'], "role": "editor"})

    groups = plugins.toolkit.get_action('group_list')(context, {})

    for group in groups:
        plugins.toolkit.get_action('group_member_create')(context, {'id': group, 'username': result['name'], 'role': 'editor'})

    return result


@logic.side_effect_free
def action_organization_show(context, data_dict):
    try:
        result = get_original_method('ckan.logic.action.get', 'organization_show')(context, data_dict)
    except NotAuthorized:
        raise NotFound

    result['display_name'] = extra_translation(result, 'title') or result.get('display_name', None) or result.get('name', None)
    return result


class YtpOrganizationsPlugin(plugins.SingletonPlugin, DefaultOrganizationForm, YtpMainTranslation):
    """ CKAN plugin to change how organizations work """
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')

    _localized_fields = ['title', 'description', 'alternative_name', 'street_address', 'street_address_pobox',
                         'street_address_zip_code', 'street_address_place_of_business', 'street_address_country',
                         'street_address_unofficial_name', 'street_address_building_id', 'street_address_getting_there',
                         'street_address_parking', 'street_address_public_transport', 'street_address_url_public_transport',
                         'homepage']

    def configure(self, config):
        _configure(config)

    def get_auth_functions(self):
        return {'organization_create': auth.organization_create}

    def get_actions(self):
        return {'user_create': action_user_create, 'organization_show': action_organization_show}

    def before_map(self, map):
        organization_controller = 'ckanext.ytp.controller:YtpOrganizationController'

        with SubMapper(map, controller=organization_controller) as m:
            m.connect('organization_members', '/organization/members/{id}', action='members', ckan_icon='group')
            m.connect('/user_list', action='user_list', ckan_icon='user')
            m.connect('/admin_list', action='admin_list', ckan_icon='user')

        map.connect('/organization/new',
                    controller=organization_controller,
                    action='new')

        map.connect('organization_read_extended',
                    '/organization/{id}',
                    controller=organization_controller,
                    action='read',
                    ckan_icon='group')

        map.connect('organization_embed',
                    '/organization/{id}/embed',
                    controller=organization_controller,
                    action='embed',
                    ckan_icon='group')

        return map

    # IValidators
    def get_validators(self):
        return {
            "is_admin_in_parent_if_changed": validators.is_admin_in_parent_if_changed,
            "extra_validators_multiple_choice": validators.extra_validators_multiple_choice,
            'admin_only_feature': validators.admin_only_feature
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "get_last_harvested_date": get_last_harvested_date
        }


class YtpReportPlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(IReport)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITranslation)

    # IReport

    def register_reports(self):
        import reports
        return [
            reports.administrative_branch_summary_report_info,
            reports.deprecated_datasets_report_info,
            reports.harvester_report_info
        ]

    def update_config(self, config):
        from ckan.plugins import toolkit
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
        toolkit.add_template_directory(config, '/var/www/resources/templates')
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_resource('/var/www/resources', 'ytp_resources')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/javascript', 'theme_javascript')
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
        parsed_url = urlparse.urlparse(current_url)
        for patterns, handler, selected in self._menu_map:
            for pattern in patterns:
                if type(pattern) in types.StringTypes:
                    values = {'language': language}
                    if c.user:
                        values['username'] = c.user
                    try:
                        pattern_url = urlparse.urlparse(pattern % values)

                        if parsed_url.path == pattern_url.path:
                            skip = False
                            if pattern_url.query:
                                parsed_parameters = urlparse.parse_qs(parsed_url.query)
                                if not parsed_parameters:
                                    skip = True
                                else:
                                    for key, value in urlparse.parse_qs(pattern_url.query).iteritems():
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
        lang = helpers.lang() if helpers.lang() else "fi"  # Finnish as default language
        import requests
        import hashlib

        try:
            # Call our custom Drupal API to get drupal block content
            hostname = config.get('ckan.site_url', '')
            domains = config.get('ckanext.drupal8.domain').split(",")
            verify_cert = config.get('ckanext.drupal8.development_cert', '') or True
            cookies = {}
            for domain in domains:
                # Split domain from : and expect first part to be hostname and second part be port.
                # Here we ignore the port as drupal seems to ignore the port when generating cookiename hashes
                domain_hash = hashlib.sha256(domain.split(':')[0]).hexdigest()[:32]
                cookienames = (template % domain_hash for template in ('SESS%s', 'SSESS%s'))
                named_cookies = ((name, p.toolkit.request.cookies.get(name)) for name in cookienames)
                for cookiename, cookie in named_cookies:
                    if cookie is not None:
                        cookies.update({cookiename: cookie})

            response = requests.get('%s/%s/%s' % (hostname, lang, path), cookies=cookies, verify=verify_cert)
            return response.text
        except requests.exceptions.RequestException, e:
            log.error('%s' % e)
            return ''
        except Exception, e:
            log.error('%s' % e)
            return ''

        return None

    def _drupal_footer(self):
        return self._drupal_snippet('api/footer')

    def _drupal_header(self):
        result = self._drupal_snippet('api/header')
        if result:
            # Path variable depends on request type
            path = request.full_path if is_flask_request() else request.path_qs
            try:
                path = path.decode('utf8')
            except UnicodeDecodeError:
                path = path.decode('cp1252')
            # Language switcher links will point to /api/header, fix them based on currently requested page
            return re.sub(u'href="/(\\w+)/api/header"', u'href="/data/\\1%s"' % path, result)
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
        user = model.User.get(unicode(user))
        if not user:
            return user_name
        else:
            user_id = user.id
            user_name = user.name
            user_displayname = user.display_name

    if not model.User.VALID_NAME.match(user_name):
        user_name = user_id

    if maxlength and len(user_displayname) > maxlength:
        user_displayname = user_displayname[:maxlength] + '...'
    return link_to(user_displayname, helpers.url_for(controller='user', action='read', id=user_name), class_='')


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
        toolkit.add_resource('public/javascript/', 'ytp_common_js')
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
            labels.append(u'showcase-admin')

        return labels

    def get_user_dataset_labels(self, user_obj):
        '''
        Showcase admin users get a showcase-admin label
        '''
        # Default labels
        labels = super(YtpIPermissionLabelsPlugin, self).get_user_dataset_labels(user_obj)

        if user_obj and ShowcaseAdmin.is_user_showcase_admin(user_obj):
            labels.append(u'showcase-admin')

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
