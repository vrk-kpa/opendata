from ckan import plugins, model
from ckan.plugins import toolkit
from ckan.lib.navl.dictization_functions import Missing
from ckan.lib import helpers
from ckan.common import _, c, request

from webhelpers.html import escape
from pylons import config

from ckanext.ytp.dataset.converters import date_validator
from ckanext.ytp.common.converters import to_list_json, from_json_list, is_url, convert_to_tags_string, string_join

import types
import re
import logging
from ckanext.ytp.dataset.helpers import service_database_enabled
from ckanext.ytp.common.tools import add_languages_modify, add_languages_show, add_translation_show_schema, add_translation_modify_schema


try:
    from collections import OrderedDict  # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

log = logging.getLogger(__name__)


OPEN_DATA = 'Open Data'
INTEROPERABILITY_TOOLS = 'Interoperability Tools'
PUBLIC_SERVICES = 'Public Services'


def _escape(value):
    return escape(unicode(value))


def _prettify(field_name):
    """ Taken from ckan.logic.ValidationError.error_summary """
    field_name = re.sub('(?<!\w)[Uu]rl(?!\w)', 'URL', field_name.replace('_', ' ').capitalize())
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


def set_to_user_name(value, context):
    return context['auth_user_obj'].display_name


def set_to_user_email(value, context):
    return context['auth_user_obj'].email


_key_functions = {u'extras':  _parse_extras}


class YTPDatasetForm(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.interfaces.IFacets, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)

    _collection_mapping = {None: ("package/ytp/new_select.html", 'package/new_package_form.html'),
                           OPEN_DATA: ('package/new.html', 'package/new_package_form.html'),
                           INTEROPERABILITY_TOOLS: ('package/new.html', 'package/new_package_form.html')}

    _localized_fields = ['title', 'notes', 'copyright_notice', 'warranty_disclaimer']

    _key_exclude = ['resources', 'organization', 'copyright_notice', 'warranty_disclaimer', 'license_url', 'name',
                    'version', 'state', 'notes', 'tags', 'title', 'collection_type', 'license_title', 'extra_information',
                    'maintainer', 'author', 'num_tags', 'owner_org', 'type', 'license_id', 'num_resources',
                    'temporal_granularity', 'temporal_coverage_from', 'temporal_coverage_to', 'update_frequency']
    # IRoutes #

    def after_show(self, context, pkg_dict):
        if u'resources' in pkg_dict and pkg_dict[u'resources']:
            for resource in pkg_dict[u'resources']:
                if 'url_type' in resource and isinstance(resource['url_type'], Missing):
                    resource['url_type'] = None

    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        controller = 'ckanext.ytp.dataset.controller:YtpDatasetController'
        m.connect('/ytp-api/1/util/tag/autocomplete', action='ytp_tag_autocomplete',
                  controller=controller,
                  conditions=dict(method=['GET']))
        m.connect('/dataset/new_metadata/{id}', action='new_metadata', controller=controller)  # override metadata step at new package

        return m

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_resource('public/javascript/', 'ytp_dataset_js')
        toolkit.add_template_directory(config, 'templates')

        toolkit.add_resource('../common/public/javascript/', 'ytp_common_js')
        toolkit.add_template_directory(config, '../common/templates')

    # IDatasetForm #

    def _modify_package_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')
        not_empty = toolkit.get_validator('not_empty')
        schema = add_translation_modify_schema(schema)

        schema.update({'copyright_notice': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'warranty_disclaimer': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'collection_type': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'extra_information': [ignore_missing, is_url, to_list_json, convert_to_extras]})
        schema.update({'valid_from': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'valid_till': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'content_type': [not_empty, convert_to_tags_string('content_type')]})

        schema.update({'original_language': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'translations': [ignore_missing, to_list_json, convert_to_extras]})
        # TODO: This is not working with empty values
        # schema.update({'resources': {'temporal_coverage_from': [ignore_missing, date_validator],
        #               'temporal_coverage_to': [ignore_missing, date_validator]}})
        schema = add_languages_modify(schema, self._localized_fields)

        schema.update({'author': [set_to_user_name, ignore_missing, unicode]})
        schema.update({'author_email': [set_to_user_email, ignore_missing, unicode]})

        # Override CKAN schema
        schema.update({'notes': [not_empty, unicode]})
        schema.update({'license_id': [not_empty, unicode]})

        return schema

    def create_package_schema(self):
        schema = super(YTPDatasetForm, self).create_package_schema()
        not_empty = toolkit.get_validator('not_empty')
        tag_string_convert = toolkit.get_validator('tag_string_convert')
        schema.update({'tag_string': [not_empty, tag_string_convert]})
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
        schema.update({'warranty_disclaimer': [convert_from_extras, ignore_missing]})
        schema.update({'collection_type': [convert_from_extras, ignore_missing]})
        schema.update({'extra_information': [convert_from_extras, from_json_list, ignore_missing]})
        schema.update({'valid_from': [convert_from_extras, ignore_missing]})
        schema.update({'valid_till': [convert_from_extras, ignore_missing]})
        schema.update({'temporal_granularity': [convert_from_extras, ignore_missing]})
        schema.update({'update_frequency': [convert_from_extras, ignore_missing]})
        schema.update({'content_type': [toolkit.get_converter('convert_from_tags')('content_type'), string_join, ignore_missing]})

        schema = add_translation_show_schema(schema)
        schema = add_languages_show(schema, self._localized_fields)

        return schema

    def package_types(self):
        return []

    def is_fallback(self):
        return True

    def _get_from_mapping(self, index):
        collection_type = request.params.get('collection_type', None)
        if not collection_type and c.pkg_dict and 'collection_type' in c.pkg_dict:
            collection_type = c.pkg_dict['collection_type']

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
        super(YTPDatasetForm, self).setup_template_variables(context, data_dict)

    # IFacets #

    def dataset_facets(self, facets_dict, package_type):
        facets_dict = OrderedDict()
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict.update({'tags': _('Tags')})
        facets_dict.update({'vocab_content_type': _('Content Type')})
        facets_dict.update({'res_format': _('Formats')})
        facets_dict.update({'organization': _('Organization')})
        # add more dataset facets here
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    # ITemplateHelpers #
    def format_extras(self, extras):
        return _format_extras(extras)

    def _clean_extras(self, extras):
        extra_dict = {}
        for key in extras:
            if key not in self._key_exclude:
                value = extras.get(key)
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

    def _get_user(self, user):
        if user in [model.PSEUDO_USER__LOGGED_IN, model.PSEUDO_USER__VISITOR]:
            return user
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
        return [(u'Creative Commons CCZero 1.0', u'cc-zero-1.0'),
                (u'Creative Commons Attribution 4.0 ', u'cc-by-4.0')]

    def _locales_offered(self):
        return config.get('ckan.locales_offered', '').split()

    def _is_list(self, value):
        return isinstance(value, list)

    def _markdown(self, translation, length):
        return helpers.markdown_extract(translation, extract_length=length) if length is not True and isinstance(length, (int, long)) else \
            helpers.render_markdown(translation)

    def _extra_translation(self, values, field, markdown=False, fallback=None):
        """ Used as helper. Get correct translation from extras (values) for given field.
            If markdown is True uses markdown rendering for value. If markdown is number use markdown_extract with given value.
            If fallback is set then use fallback as value if value is empty.
            If fallback is function then call given function with `values`.
        """
        translation = values.get('%s_%s' % (field, helpers.lang()), "") or values.get(field, "") if values else ""

        if not translation and fallback:
            translation = fallback(values) if hasattr(fallback, '__call__') else fallback

        return self._markdown(translation, markdown) if markdown and translation else translation

    def _get_package(self, package):
        return toolkit.get_action('package_show')({'model': model}, {'id': package})

    def get_helpers(self):
        return {'current_user': self._current_user,
                'dataset_licenses': self._dataset_licenses,
                'get_user': self._get_user,
                'unique_formats': self._unique_formats,
                'locales_offered': self._locales_offered,
                'is_list': self._is_list,
                'format_extras': self.format_extras,
                'extra_translation': self._extra_translation,
                'service_database_enabled': service_database_enabled,
                'clean_extras': self._clean_extras,
                'get_package': self._get_package}
