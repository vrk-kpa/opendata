from pylons import config

from ckan import plugins, model
from ckan.plugins import toolkit
from ckan.lib.navl.dictization_functions import Missing
from ckan.lib import helpers
from ckan.common import _, c, request

from converters import convert_to_tags_string, date_validator, translation_string, string_join
import logging
from ckanext.ytp.common.converters import to_list_json, from_json_list, is_url
from webhelpers.html import escape, literal
import types
import re

try:
    from collections import OrderedDict  # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

log = logging.getLogger(__name__)


def organization_list_for_user(context, data_dict):
    ''' Taken from CKAN (ckan.logic.action.get). Fixes member state.
    https://github.com/ckan/ckan/issues/1596

    Return the list of organizations that the user is a member of.

    :param permission: the permission the user has against the
    returned organizations (optional, default: ``edit_group``)
    :type permission: string

    :returns: list of dictized organizations that the user is
    authorized to edit
    :rtype: list of dicts
    '''
    from ckan.logic.action.get import _check_access
    from ckan import new_authz
    from ckan.lib.dictization import model_dictize

    current_model = context['model']
    user = context['user']

    _check_access('organization_list_for_user', context, data_dict)
    sysadmin = new_authz.is_sysadmin(user)

    orgs_q = current_model.Session.query(model.Group) \
        .filter(current_model.Group.is_organization == True) \
        .filter(current_model.Group.state == 'active')  # noqa

    if not sysadmin:
        # for non-Sysadmins check they have the required permission

        permission = data_dict.get('permission', 'edit_group')

        roles = new_authz.get_roles_with_permission(permission)

        if not roles:
            return []
        user_id = new_authz.get_user_id_for_username(user, allow_none=True)
        if not user_id:
            return []

        q = current_model.Session.query(current_model.Member) \
            .filter(current_model.Member.table_name == 'user') \
            .filter(current_model.Member.capacity.in_(roles)) \
            .filter(current_model.Member.table_id == user_id) \
            .filter(current_model.Member.state == 'active')

        group_ids = []
        for row in q.all():
            group_ids.append(row.group_id)

        if not group_ids:
            return []

        orgs_q = orgs_q.filter(current_model.Group.id.in_(group_ids))

    orgs_list = model_dictize.group_list_dictize(orgs_q.all(), context)
    return orgs_list


def _escape(value):
    return escape(unicode(value))


def _list_to_ul(items):
    ul_buffer = ["<ul class='dataset-extra'>"]
    for item in items:
        ul_buffer.append("<li>%s</li>" % item)
    ul_buffer.append("</ul>")
    return "\n".join(ul_buffer)


def _to_link(value):
    if not isinstance(value, list):
        value = [value]
    link_buffer = []
    for item in value:
        if item:
            link_buffer.append('<a href="%s">%s</a>' % (_escape(item), _escape(item)))
    return _list_to_ul(link_buffer)


class YTPDatasetForm(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.interfaces.IFacets, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)

    _collection_mapping = {None: "package/ytp/new_select.html", 'Open Data': 'package/new.html',
                           'Interoperability Tools': 'package/new.html', 'Public Services': 'package/new.html'}

    _key_mappings = {'extra_information': ('Extra information at website', _to_link)}
    _key_exclude = ['resources', 'organization', 'author_email', 'author', 'maintainer_email', 'maintainer', 'version', 'state']

    # IRoutes #

    def after_show(self, context, pkg_dict):
        if u'resources' in pkg_dict and pkg_dict[u'resources']:
            for resource in pkg_dict[u'resources']:
                if 'url_type' in resource and isinstance(resource['url_type'], Missing):
                    resource['url_type'] = None

    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        m.connect('/ytp-api/1/util/tag/autocomplete', action='ytp_tag_autocomplete',
                  controller='ckanext.ytp.dataset.controller:YtpDatasetController',
                  conditions=dict(method=['GET']))
        return m

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_resource('public/javascript/', 'ytp_dataset_js')
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('../common/public/javascript/', 'ytp_common_js')

    # IDatasetForm #

    def _add_languages_modify(self, schema, field, locales):
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')
        for locale in locales:
            schema.update({"%s_%s" % (field, locale): [ignore_missing, translation_string(field), unicode, convert_to_extras]})
        return schema

    def _add_languages_show(self, schema, field, locales):
        for locale in locales:
            schema.update({"%s_%s" % (field, locale): [toolkit.get_converter('convert_from_extras'), toolkit.get_validator('ignore_missing')]})
        return schema

    def _modify_package_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')

        schema.update({'copyright_notice': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'warranty_disclaimer': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'collection_type': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'extra_information': [ignore_missing, is_url, to_list_json, convert_to_extras]})
        schema.update({'valid_from': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'valid_till': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'content_type': [ignore_missing, convert_to_tags_string('content_type')]})

        schema.update({'title_locale': [ignore_missing, unicode, convert_to_extras]})
        locales = [locale.language for locale in helpers.get_available_locales()]

        self._add_languages_modify(schema, 'title', locales)

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
        schema.update({'warranty_disclaimer': [convert_from_extras, ignore_missing]})
        schema.update({'collection_type': [convert_from_extras, ignore_missing]})
        schema.update({'extra_information': [convert_from_extras, from_json_list, ignore_missing]})
        schema.update({'valid_from': [convert_from_extras, ignore_missing]})
        schema.update({'valid_till': [convert_from_extras, ignore_missing]})
        schema.update({'content_type': [toolkit.get_converter('convert_from_tags')('content_type'), string_join, ignore_missing]})

        schema.update({'title_locale': [convert_from_extras, ignore_missing]})
        locales = [locale.language for locale in helpers.get_available_locales()]

        self._add_languages_show(schema, 'title', locales)

        return schema

    def package_types(self):
        return []

    def is_fallback(self):
        return True

    def new_template(self):
        template = self._collection_mapping.get(request.params.get('collection_type', None), None)
        if not template:
            c.unknown_collection = True
            return self._collection_mapping.get(None)
        return template

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
        return [('', ''), (u'License Not Specified', u'notspecified'),
                (u'Creative Commons CCZero 1.0', u'cc-zero-1.0'),
                (u'Creative Commons Attribution 4.0 ', u'cc-by-4.0')]

    def _locales_offered(self):
        return config.get('ckan.locales_offered', '').split()

    def _is_list(self, value):
        return isinstance(value, list)

    def _prettify(self, field_name):
        """ Taken from ckan.logic.ValidationError.error_summary """
        field_name = re.sub('(?<!\w)[Uu]rl(?!\w)', 'URL', field_name.replace('_', ' ').capitalize())
        return _(field_name.replace('_', ' '))

    def _translate_key(self, key):
        value = self._key_mappings.get(key, None)
        return _escape(_(value[0]) if value else self._prettify(key)), value[1] if value else None

    def _format_value(self, value):
        if isinstance(value, types.DictionaryType):
            value_buffer = []
            for key, item_value in value.iteritems():
                value_buffer.append(u"%s: %s" % (_escape(key), self._format_value(item_value)))
            return _list_to_ul(value_buffer)
        elif isinstance(value, types.ListType):
            value_buffer = []
            for item_value in value:
                value_buffer.append(self._format_value(item_value))
            return _list_to_ul(value_buffer)

        return _escape(value)

    def _format_extras(self, extras):
        if not extras:
            return ""
        extra_buffer = []
        for extra_key, extra_value in extras.iteritems():
            if extra_key in self._key_exclude:
                continue
            key, value_formatter = self._translate_key(extra_key)
            value = None
            if value_formatter:
                value = value_formatter(extra_value)
            else:
                value = self._format_value(extra_value).strip()
            if key and value:
                extra_buffer.append(u'<dt>%s</dt><dd>%s</dd>' % (key, value))

        return literal("<dl>" + "\n".join(extra_buffer) + "</dl>")

    def get_helpers(self):
        return {'current_user': self._current_user,
                'dataset_licenses': self._dataset_licenses,
                'get_user': self._get_user,
                'unique_formats': self._unique_formats,
                'locales_offered': self._locales_offered,
                'is_list': self._is_list,
                'format_extras': self._format_extras}

    # IActions #

    def get_actions(self):
        return {'organization_list_for_user': organization_list_for_user}
