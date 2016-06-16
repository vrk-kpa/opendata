from ckan import plugins, model, logic
from ckan.plugins import toolkit
from ckan.lib.navl.dictization_functions import Missing, StopOnError, missing, flatten_dict, unflatten
from ckan.lib import helpers
from ckan.lib.munge import munge_title_to_name
from ckan.logic import get_action, NotFound
from ckan.common import _, c, request
from ckan.model import Session
from ckan import new_authz as authz
from webhelpers.html import escape
from pylons import config

from ckanext.ytp.dataset.converters import date_validator, simple_date_validate
from ckanext.ytp.common.converters import to_list_json, from_json_list, is_url, convert_to_tags_string, string_join

import types
import re
import logging
from ckanext.ytp.dataset.helpers import service_database_enabled, get_json_value, sort_datasets_by_state_priority, get_facet_item_count, \
    get_remaining_facet_item_count, sort_facet_items_by_name, get_sorted_facet_items_dict, calculate_dataset_stars, get_upload_size, \
    get_license, get_visits_for_resource, get_visits_for_dataset, get_geonetwork_link, calculate_metadata_stars, get_tooltip_content_types, \
    unquote_url, sort_facet_items_by_count
from ckanext.ytp.common.tools import add_languages_modify, add_languages_show, add_translation_show_schema, add_translation_modify_schema, get_original_method
from ckanext.ytp.common.helpers import extra_translation, render_date
from paste.deploy.converters import asbool
from ckanext.spatial.interfaces import ISpatialHarvester
from ckanext.ytp.dataset import auth

import json

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


class YTPDatasetForm(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.interfaces.IFacets, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(ISpatialHarvester, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

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
        self.auto_author = asbool(config.get('ckanext.ytp.dataset.auto_author', False))

    # IRoutes #

    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        controller = 'ckanext.ytp.dataset.controller:YtpDatasetController'
        m.connect('/ytp-api/1/util/tag/autocomplete', action='ytp_tag_autocomplete',
                  controller=controller,
                  conditions=dict(method=['GET']))
        m.connect('/dataset/new_metadata/{id}', action='new_metadata', controller=controller)  # override metadata step at new package
        m.connect('dataset_edit', '/dataset/edit/{id}', action='edit', controller=controller, ckan_icon='edit')
        m.connect('new_resource', '/dataset/new_resource/{id}', action='new_resource', controller=controller, ckan_icon='new')
        m.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}', action='resource_edit', controller=controller, ckan_icon='edit')

        # Mapping of new dataset is needed since, remapping on read overwrites it
        m.connect('add dataset', '/dataset/new', controller='package', action='new')
        m.connect('/dataset/{id}.{format}', action='read', controller=controller)
        m.connect('related_new', '/dataset/{id}/related/new', action='new_related', controller=controller)
        m.connect('related_edit', '/dataset/{id}/related/edit/{related_id}',
                  action='edit_related', controller=controller)
        m.connect('dataset_read', '/dataset/{id}', action='read', controller=controller, ckan_icon='sitemap')
        m.connect('/api/util/dataset/autocomplete_by_collection_type', action='autocomplete_packages_by_collection_type', controller=controller)
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
        schema.update({'content_type': [toolkit.get_converter('convert_from_tags')('content_type'), string_join, ignore_missing]})
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

        This method can be used to identify which collection the user is currently looking at or editing, i.e., which page the user is on.
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
        facets_dict = OrderedDict()
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict.update({'tags': _('Tags')})
        facets_dict.update({'vocab_content_type': _('Content Type')})
        facets_dict.update({'organization': _('Organization')})
        facets_dict.update({'res_format': _('Formats')})
        # BFW: source is not part of the schema. created artificially at before_index function
        facets_dict.update({'source': _('Source')})
        # add more dataset facets here
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):

        facets_dict = OrderedDict()
        facets_dict.update({'collection_type': _('Collection Type')})
        facets_dict.update({'tags': _('Tags')})
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
                value = extras.get(key)
                if value:
                    extra_dict.update({_prettify(key): value})
        return extra_dict

    def _clean_extras_resources(self, extras):
        extra_dict = {}
        for key in extras:
            if key not in self._key_exclude_resources:
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

    def _get_user_by_id(self, user_id):
        if not user_id:
            return None
        else:
            user = model.User.get(user_id)
            return user.name

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
        value = helpers.resource_display_name(resource_dict)
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
                'get_geonetwork_link': get_geonetwork_link,
                'get_tooltip_content_types': get_tooltip_content_types,
                'unquote_url': unquote_url}

    def get_auth_functions(self):
        return {'related_update': auth.related_update,
                'related_create': auth.related_create}

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
        return pkg_dict

    # IActions #
    def get_actions(self):
        return {'package_show': action_package_show}

    # ISpatialHarvester

    def get_package_dict(self, context, data_dict):

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
                    elif extra['value'] == 'series':
                        value = 'paikkatietoaineistosarja'
                    elif extra['value'] == 'service':
                        value = 'paikkatietopalvelu'
                        for temp_extra in package_dict['extras']:
                            if temp_extra['key'] == 'collection_type':
                                temp_extra['value'] = 'Interoperability Tools'
                    else:
                        continue

                    package_dict['content_type'] = value
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

        # topic category for syke

        topic_categories = data_dict['iso_values'].get('topic-category')
        if topic_categories:
            for category in topic_categories:
                category = category[:50] if len(category) > 50 else category
                package_dict['tags'].append({'name': category})

        return package_dict
