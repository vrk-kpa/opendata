import ast
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
from ckan.lib.navl import dictization_functions
from ckan.lib.navl.dictization_functions import Missing, StopOnError, missing, flatten_dict, unflatten, Invalid
from ckan.lib.plugins import DefaultOrganizationForm, DefaultTranslation
from ckan.logic import NotFound, NotAuthorized, get_action
from ckan.model import Session
from ckan.plugins import toolkit
from ckan.plugins.toolkit import config
from ckanext.report.interfaces import IReport
from ckanext.spatial.interfaces import ISpatialHarvester

from paste.deploy.converters import asbool
from webhelpers.html import escape
from webhelpers.html.builder import literal
from webhelpers.html.tags import link_to

import auth
import menu

from converters import to_list_json, from_json_list, is_url, \
     convert_to_tags_string, string_join, date_validator, simple_date_validate

from helpers import extra_translation, render_date, service_database_enabled, get_json_value, \
    sort_datasets_by_state_priority, get_facet_item_count, get_remaining_facet_item_count, sort_facet_items_by_name, \
    get_sorted_facet_items_dict, calculate_dataset_stars, get_upload_size, get_license, get_visits_for_resource, \
    get_visits_for_dataset, get_geonetwork_link, calculate_metadata_stars, get_tooltip_content_types, unquote_url, \
    sort_facet_items_by_count, scheming_field_only_default_required, add_locale_to_source, scheming_language_text_or_empty, \
    get_lang_prefix, call_toolkit_function, get_translated, dataset_display_name, resource_display_name, \
    get_visits_count_for_dataset_during_last_year, get_current_date, get_download_count_for_dataset_during_last_year
from tools import create_system_context, get_original_method, add_translation_show_schema, add_languages_show, \
    add_translation_modify_schema, add_languages_modify


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


def set_empty_if_missing(value, context):
    return value if value else u""


def set_to_user_name(value, context):
    return context['auth_user_obj'].display_name


def set_to_user_email(value, context):
    return context['auth_user_obj'].email


def not_value(text_value):
    def callback(key, data, errors, context):
        value = data.get(key)
        if value == text_value:
            errors[key].append(_('Missing value'))
            raise StopOnError
    return callback


def not_empty_or(item):
    def callback(key, data, errors, context):
        value = data.get(key)
        if value == "":
            # tag_string is converted to tags, so we need check if value is given as empty
            errors[key].append(_('Missing value'))
            raise StopOnError
        elif not value or value is missing:
            value = data.get((item, 0, u'name'), None)
            if not value or value is missing:
                errors[key].append(_('Missing value'))
            else:
                data.pop(key, None)
            raise StopOnError
    return callback


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

    _collection_mapping = {None: ("package/ytp/new_select.html", 'package/new_package_form.html'),
                           OPEN_DATA: ('package/new.html', 'package/new_package_form.html'),
                           INTEROPERABILITY_TOOLS: ('package/new.html', 'package/new_package_form.html')}

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

    def _modify_package_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')
        not_empty = toolkit.get_validator('not_empty')
        schema = add_translation_modify_schema(schema)

        schema.update({'copyright_notice': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'collection_type': [not_empty, unicode, convert_to_extras]})
        schema.update({'extra_information': [ignore_missing, is_url, to_list_json, convert_to_extras]})
        schema.update({'valid_from': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'valid_till': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'content_type': [not_empty, convert_to_tags_string('content_type')]})

        schema.update({'original_language': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'translations': [ignore_missing, to_list_json, convert_to_extras]})

        schema.update({'owner': [set_empty_if_missing, unicode, convert_to_extras]})
        schema.update({'maintainer': [set_empty_if_missing, unicode]})
        schema.update({'maintainer_email': [set_empty_if_missing, unicode]})

        res_schema = schema.get('resources')
        res_schema.update({'temporal_coverage_from': [ignore_missing, simple_date_validate],
                           'temporal_coverage_to': [ignore_missing, simple_date_validate]})
        schema.update({'resources': res_schema})
        schema = add_languages_modify(schema, self._localized_fields)

        if not self.auto_author or c.userobj.sysadmin:
            schema.update({'author': [set_empty_if_missing, unicode]})
            schema.update({'author_email': [set_empty_if_missing, unicode]})
        else:
            schema.update({'author': [set_to_user_name, ignore_missing, unicode]})
            schema.update({'author_email': [set_to_user_email, ignore_missing, unicode]})

        # Override CKAN schema
        schema.update({'title': [not_empty, unicode]})
        schema.update({'notes': [not_empty, unicode]})
        schema.update({'license_id': [not_empty, not_value('notspecified'), unicode]})

        tag_string_convert = toolkit.get_validator('tag_string_convert')
        schema.update({'tag_string': [not_empty_or('tags'), tag_string_convert]})

        return schema

    def create_package_schema(self):
        schema = super(YTPDatasetForm, self).create_package_schema()
        return self._modify_package_schema(schema)

    def update_package_schema(self):
        schema = super(YTPDatasetForm, self).update_package_schema()
        return self._modify_package_schema(schema)

    def show_package_schema(self):
        schema = super(YTPDatasetForm, self).show_package_schema()

        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_from_extras = toolkit.get_converter('convert_from_extras')

        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))

        schema.update({'copyright_notice': [convert_from_extras, ignore_missing]})
        schema.update({'collection_type': [convert_from_extras, ignore_missing]})
        schema.update({'extra_information': [convert_from_extras, from_json_list, ignore_missing]})
        schema.update({'valid_from': [convert_from_extras, ignore_missing]})
        schema.update({'valid_till': [convert_from_extras, ignore_missing]})
        schema.update({'temporal_granularity': [convert_from_extras, ignore_missing]})
        schema.update({'update_frequency': [convert_from_extras, ignore_missing]})
        schema.update({'content_type': [toolkit.get_converter('convert_from_tags')
                                        ('content_type'), string_join, ignore_missing]})
        schema.update({'owner': [convert_from_extras, ignore_missing]})

        schema = add_translation_show_schema(schema)
        schema = add_languages_show(schema, self._localized_fields)

        return schema

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

    def _get_from_mapping(self, index):
        # Get the collection type so that we know which template to show
        collection_type = self._get_collection_type()

        template = self._collection_mapping.get(collection_type, None)
        if not template:
            c.unknown_collection = True
            return self._collection_mapping.get(None)[index]
        return template[index]

    def new_template(self):
        return self._get_from_mapping(0)

    def package_form(self):
        return self._get_from_mapping(1)

    def setup_template_variables(self, context, data_dict):
        c.preselected_group = request.params.get('group', None)
        try:
            super(YTPDatasetForm, self).setup_template_variables(context, data_dict)
        except Exception as e:
            if 'file:///srv/ytp/files/ckan/license.json' in e.message:
                log.info(e)
                pass
            else:
                raise

    # IFacets #

    def dataset_facets(self, facets_dict, package_type):
        lang = get_lang_prefix()
        facets_dict = OrderedDict()
        facets_dict.update({'vocab_international_benchmarks': _('International benchmarks')})
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict['vocab_keywords_' + lang] = _('Popular tags')
        facets_dict.update({'vocab_content_type': _('Content Type')})
        facets_dict.update({'organization': _('Organization')})
        facets_dict.update({'res_format': _('Formats')})
        # BFW: source is not part of the schema. created artificially at before_index function
        facets_dict.update({'source': _('Source')})
        facets_dict.update({'license_id': _('License')})
        # add more dataset facets here
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
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

    def _clean_extras(self, extras):
        extra_dict = {}
        for key in extras:
            if key not in self._key_exclude:
                value = get_translated(extras, key)
                if value:
                    extra_dict.update({_prettify(key): value})
        return extra_dict

    def _clean_extras_resources(self, extras):
        extra_dict = {}
        for key in extras:
            if key not in self._key_exclude_resources:
                value = get_translated(extras, key)
                if value:
                    extra_dict.update({_prettify(key): value})
        return extra_dict

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

    def _dataset_licenses(self):
        licenses_list = [(u'Creative Commons CCZero 1.0', u'cc-zero-1.0'),
                         (u'Creative Commons Attribution 4.0 ', u'cc-by-4.0'),
                         (_('Other'), u'other')]

        return licenses_list

    def _locales_offered(self):
        return config.get('ckan.locales_offered', '').split()

    def _is_list(self, value):
        return isinstance(value, list)

    def _get_package(self, package):
        return toolkit.get_action('package_show')({'model': model}, {'id': package})

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
                'dataset_licenses': self._dataset_licenses,
                'get_user': self._get_user,
                'unique_formats': self._unique_formats,
                'locales_offered': self._locales_offered,
                'is_list': self._is_list,
                'format_extras': self.format_extras,
                'extra_translation': extra_translation,
                'service_database_enabled': service_database_enabled,
                'clean_extras': self._clean_extras,
                'clean_extras_resources': self._clean_extras_resources,
                'get_package': self._get_package,
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
                'dataset_display_name': dataset_display_name}

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
        translated_vocabs = ['keywords']
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
        return {'package_show': action_package_show}

    # IValidators
    def get_validators(self):
        return {
            'lower_if_exists': validators.lower_if_exists,
            'upper_if_exists': validators.upper_if_exists,
            'tag_string_or_tags_required': validators.tag_string_or_tags_required,
            'create_tags': validators.create_tags,
            'create_fluent_tags': validators.create_fluent_tags,
            'set_private_if_not_admin': validators.set_private_if_not_admin,
            'list_to_string': validators.list_to_string,
            'convert_to_list': validators.convert_to_list,
            'tag_list_output': validators.tag_list_output,
            'repeating_text': validators.repeating_text,
            'repeating_text_output': validators.repeating_text_output,
            'only_default_lang_required': validators.only_default_lang_required,
            'keep_old_value_if_missing': validators.keep_old_value_if_missing,
            'override_field': validators.override_field,
            'override_field_with_default_translation': validators.override_field_with_default_translation,
            'ignore_if_invalid_isodatetime': validators.ignore_if_invalid_isodatetime,
            'from_date_is_before_until_date': validators.from_date_is_before_until_date
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


def _user_has_organization(username):
    user = model.User.get(username)
    if not user:
        raise NotFound("Failed to find user")
    query = model.Session.query(model.Member).filter(model.Member.table_name ==
                                                     'user').filter(model.Member.table_id == user.id)
    return query.count() > 0


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
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IValidators)

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

    def group_title_validator(self, key, data, errors, context):
        """ Validator to prevent duplicate title.
            See ckan.logic.schema
        """
        contect_model = context['model']
        session = context['session']
        group = context.get('group')

        query = session.query(contect_model.Group.title).filter_by(title=data[key])
        if group:
            group_id = group.id
        else:
            group_id = data.get(key[:-1] + ('id',))
        if group_id and group_id is not dictization_functions.missing:
            query = query.filter(contect_model.Group.id != group_id)
        result = query.first()
        if result:
            errors[key].append(_('Group title already exists in database'))

    # From ckanext-hierarchy
    def setup_template_variables(self, context, data_dict):
        from pylons import tmpl_context
        model = context['model']
        group_id = data_dict.get('id')

        if group_id:
            group = model.Group.get(group_id)
            tmpl_context.allowable_parent_groups = \
                group.groups_allowed_to_be_its_parent(type='organization')
        else:
            tmpl_context.allowable_parent_groups = model.Group.all(group_type='organization')

    def _get_dropdown_menu_contents(self, vocabulary_names):
        """ Gets vocabularies by name and mangles them to match data structure required by form.select """

        try:
            user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
            context = {'user': user['name']}
            menu_items = []

            for vocabulary_name in vocabulary_names:
                vocabulary = toolkit.get_action('vocabulary_show')(context, {'id': vocabulary_name})
                tags = vocabulary.get('tags')

                for tag in sorted(tags):
                    menu_items.append({'value': tag['name'], 'text': tag['display_name']})
            return menu_items
        except NotAuthorized:
            return []

    def _get_authorized_parents(self):
        """ Returns a list of organizations under which the current user can put child organizations.

        The user is required to be an admin in the parent. If the user is a sysadmin,
        then the user will see all allowable parent organizations. """

        if not c.userobj.sysadmin:
            # If the user is not a sysadmin, then show only those parent organizations in which the user is an admin
            admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active')\
                .filter(model.Member.table_name == 'user') \
                .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == c.userobj.id)

            admin_groups = []
            for admin_org in admin_in_orgs:
                if any(admin_org.group.name == non_looping_org.name for non_looping_org in c.allowable_parent_groups):
                    admin_groups.append(admin_org.group)
        else:
            # If the user is a sysadmin, then show all allowable parent organizations
            admin_groups = []
            for group in c.allowable_parent_groups:
                admin_groups.append(group)

        return admin_groups

    def _get_parent_organization_display_name(self, organization_id):
        group = [group for group in c.allowable_parent_groups if group.id == organization_id]
        if group:
            return group[0].title if group[0].title else group[0].id
        return "not_found"

    def _is_organization_in_authorized_parents(self, organization_id, parents):
        group = [group for group in parents if group.name == organization_id]
        if group:
            return True
        return False

    def get_helpers(self):
        return {'get_dropdown_menu_contents': self._get_dropdown_menu_contents,
                'get_authorized_parents': self._get_authorized_parents,
                'get_parent_organization_display_name': self._get_parent_organization_display_name,
                'is_organization_in_authorized_parents': self._is_organization_in_authorized_parents
                }

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
                    action='new',
                    controller='organization')

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


def convert_to_list(key, data):
    if isinstance(key, basestring):
        key = [key]
    return key


def convert_from_db_to_form_list(key, data):
    key = unicode(key)
    key = ast.literal_eval(key)
    for i, value in enumerate(key):
        key[i] = unicode(value)

    return key


def from_json_to_object(key, data):
    if not key:
        return key
    key = ast.literal_eval(key)
    if isinstance(key, list):
        for i, value in enumerate(key):
            try:
                parsed = json.loads(value)
                key[i] = parsed
            except TypeError:
                pass

    return key


class YtpReportPlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(IReport)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITranslation)

    # IReport

    def register_reports(self):
        import reports
        return [reports.administrative_branch_summary_report_info]

    def update_config(self, config):
        from ckan.plugins import toolkit
        toolkit.add_template_directory(config, 'templates')


def set_to_value(preset_value):
    def method(value, context):
        return preset_value
    return method


def static_value(preset_value):
    def method(value, context):
        return preset_value
    return method


def service_charge_validator(key, data, errors, context):
    """Validates the fields related to service charge.

    If the service has a charge, then the user must also supply either the pricing information URL
    or a description of the service pricing or both."""

    # Get the value for the service charge radio field
    service_charge_value = data.get(key)

    if service_charge_value is missing or service_charge_value is None or service_charge_value == '':
        # At least one of the service charge values must be selected
        raise Invalid(_('Service charge must be supplied'))
    elif service_charge_value == 'yes':
        # Check if the service has a charge
        # Get the pricing information url and service price description values from the data (the key is a tuple)
        pricing_url_value = data.get(('pricing_information_url',))
        service_price_value = data.get(('service_price_description',))

        if ((pricing_url_value is missing or pricing_url_value is None or pricing_url_value == '') and
                (service_price_value is missing or service_price_value is None or service_price_value == '')):
            # If both the pricing information url and the service price description fields are empty, show an error message
            raise Invalid(_('If there is a service charge, you must supply either the pricing information '
                            'web address for this service or a description of ' +
                            'the service pricing or both'))
    return service_charge_value


def target_groups_validator(key, data, errors, context):
    """Validates the target groups field.

    At least one of the main target groups needs to be selected."""

    target_groups_value = data.get(key)
    if target_groups_value is missing or target_groups_value is None or target_groups_value == '':
        raise Invalid(_('At least one of the main target groups must to be selected'))
    return target_groups_value


class YtpThemePlugin(plugins.SingletonPlugin, YtpMainTranslation):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)

    default_domain = None
    logos = {}

    # TODO: We should use named routes instead
    _manu_map = [(['/user/%(username)s', '/%(language)s/user/%(username)s'], menu.UserMenu, menu.MyInformationMenu),
                 (['/dashboard/organizations',
                  '/%(language)s/dashboard/organizations'],
                  menu.UserMenu,
                  menu.MyOrganizationMenu),
                 (['/dashboard/datasets', '/%(language)s/dashboard/datasets'], menu.UserMenu, menu.MyDatasetsMenu),
                 (['/user/delete-me', '/%(language)s/user/delete-me'], menu.UserMenu, menu.MyCancelMenu),
                 (['/user/edit', '/%(language)s/user/edit', '/user/edit/%(username)s', '/%(language)s/user/edit/%(username)s'],
                  menu.UserMenu, menu.MyPersonalDataMenu),
                 (['/user/activity/%(username)s',
                  '/%(language)s/user/activity/%(username)s'],
                  menu.UserMenu,
                  menu.MyInformationMenu),
                 (['/user', '/%(language)s/user'], menu.ProducersMenu, menu.ListUsersMenu),
                 (['/%(language)s/organization', '/organization'], menu.EmptyMenu, menu.OrganizationMenu),
                 (['/%(language)s/dataset/new?collection_type=Open+Data', '/dataset/new?collection_type=Open+Data'],
                  menu.PublishMenu, menu.PublishDataMenu),
                 (['/%(language)s/dataset/new?collection_type=Interoperability+Tools',
                   '/dataset/new?collection_type=Interoperability+Tools'],
                  menu.PublishMenu, menu.PublishToolsMenu),
                 (['/%(language)s/service/new', '/service/new'],
                  menu.PublishMenu, menu.PublishServiceMenu),
                 (['/%(language)s/postit/return', '/postit/return'], menu.ProducersMenu, menu.PostitNewMenu),
                 (['/%(language)s/postit/new', '/postit/new'], menu.ProducersMenu, menu.PostitNewMenu)]

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
        for patterns, handler, selected in self._manu_map:
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

    def _site_logo(self, hostname, default=None):

        if "avoindata" in hostname:
            hostname = "avoindata"
        elif "opendata" in hostname:
            hostname = "opendata"

        lang = helpers.lang() if helpers.lang() else "default"
        dict_key = hostname + "_" + lang

        logo = self.logos.get(dict_key, self.logos.get('default', None))

        if logo:
            return literal('<img src="%s" class="site-logo" />' % helpers.url_for_static("/images/logo/%s" % logo))
        else:
            return self._short_domain(hostname, default)

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
                domain_hash = hashlib.sha256(domain).hexdigest()[:32]
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
                'site_logo': self._site_logo, 'drupal_footer': self._drupal_footer, 'drupal_header': self._drupal_header}


def helper_is_pseudo(user):
    """ Check if user is pseudo user """
    return user in [model.PSEUDO_USER__LOGGED_IN, model.PSEUDO_USER__VISITOR]


def helper_linked_user(user, maxlength=0, avatar=20):
    """ Return user as HTML item """
    if not isinstance(user, model.User):
        user_name = unicode(user)
        user = model.User.get(user_name)
        if not user:
            return user_name
    if user:
        name = user.name if model.User.VALID_NAME.match(user.name) else user.id
        displayname = user.display_name
        if maxlength and len(user.display_name) > maxlength:
            displayname = displayname[:maxlength] + '...'
        return link_to(displayname, helpers.url_for(controller='user', action='read', id=name), class_='')


def helper_organizations_for_select():
    organizations = [{'value': organization['id'],
                      'text': organization['display_name']} for organization in helpers.organizations_available()]
    return [{'value': '', 'text': ''}] + organizations


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
        return {'linked_user': helper_linked_user,
                'organizations_for_select': helper_organizations_for_select,
                'is_pseudo': helper_is_pseudo}

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
