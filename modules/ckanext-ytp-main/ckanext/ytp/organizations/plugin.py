import ckan.logic.schema
from ckan import plugins, model
from ckan.lib.plugins import DefaultOrganizationForm
from ckan.lib.navl import dictization_functions
from ckan.lib.navl.dictization_functions import Invalid
from ckan.common import _, c
from ckan.logic import NotFound, NotAuthorized
from ckan.plugins import toolkit
import ckan.lib.base as base
from ckanext.ytp.organizations import auth
from ckanext.ytp.common.tools import create_system_context, get_original_method, add_translation_show_schema, add_languages_show, \
    add_translation_modify_schema, add_languages_modify
import json
import logging
import pylons
import ast
import datetime
from ckanext.ytp.common.helpers import extra_translation
from ckan.config.routing import SubMapper

abort = base.abort

log = logging.getLogger(__name__)

# This plugin is designed to work only these versions of CKAN
plugins.toolkit.check_ckan_version(min_version='2.0')


_config_template = "ckanext.ytp.organizations.%s"
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
    query = model.Session.query(model.Member).filter(model.Member.table_name == 'user').filter(model.Member.table_id == user.id)
    return query.count() > 0


def _create_default_organization(context, organization_name, organization_title):
    values = {'name': organization_name, 'title': organization_title, 'id': organization_name}
    try:
        return plugins.toolkit.get_action('organization_show')(context, values)
    except NotFound:
        return plugins.toolkit.get_action('organization_create')(context, values)


def action_user_create(context, data_dict):
    _configure()

    result = get_original_method('ckan.logic.action.create', 'user_create')(context, data_dict)
    context = create_system_context()
    organization = _create_default_organization(context, _default_organization_name, _default_organization_title)
    plugins.toolkit.get_action('organization_member_create')(context, {"id": organization['id'], "username": result['name'], "role": "editor"})

    return result


def action_organization_show(context, data_dict):
    try:
        result = get_original_method('ckan.logic.action.get', 'organization_show')(context, data_dict)
    except NotAuthorized:
        raise NotFound

    result['display_name'] = extra_translation(result, 'title') or result.get('display_name', None) or result.get('name', None)
    return result


class YtpOrganizationsPlugin(plugins.SingletonPlugin, DefaultOrganizationForm):
    """ CKAN plugin to change how organizations work """
    plugins.implements(plugins.IGroupForm, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    plugins.implements(plugins.IConfigurer, inherit=True)

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

    def is_fallback(self):
        """ See IGroupForm.is_fallback """
        return False

    def group_types(self):
        """ See IGroupForm.group_types """
        return ['organization']

    def form_to_db_schema_options(self, options):
        """ See DefaultGroupForm.form_to_db_schema_options
            Inserts duplicate title validation to schema.
        """
        schema = super(YtpOrganizationsPlugin, self).form_to_db_schema_options(options)
        schema['title'].append(self.group_title_validator)
        return schema

    def form_to_db_schema(self):
        schema = super(YtpOrganizationsPlugin, self).form_to_db_schema()
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')

        # schema for homepages
        # schema.update({'homepages': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'homepage': [ignore_missing, unicode, convert_to_extras]})

        schema.update({'public_adminstration_organization': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'producer_type': [ignore_missing, unicode, convert_to_extras]})

        # schema for extra org info
        # schema.update({'business_id': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'oid': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'alternative_name': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'valid_from': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'valid_till': [ignore_missing, date_validator, convert_to_extras]})

        # schema for organisation address
        schema.update({'street_address': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_pobox': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'street_address_zip_code': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'street_address_place_of_business': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_country': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_unofficial_name': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_building_id': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_getting_there': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_parking': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_public_transport': [ignore_missing, unicode, convert_to_extras]})
        # schema.update({'street_address_url_public_transport': [ignore_missing, unicode, convert_to_extras]})

        schema = add_translation_modify_schema(schema)
        schema = add_languages_modify(schema, self._localized_fields)

        return schema

    def db_to_form_schema(self):
        schema = ckan.logic.schema.group_form_schema()
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_from_extras = toolkit.get_converter('convert_from_extras')

        # add following since they are missing from schema
        schema.update({'num_followers': [ignore_missing]})
        schema.update({'package_count': [ignore_missing]})

        # Schema for homepages
        schema.update({'homepage': [convert_from_extras, ignore_missing]})

        # schema for extra org info
        schema.update({'valid_from': [convert_from_extras, ignore_missing]})
        schema.update({'valid_till': [convert_from_extras, ignore_missing]})

        # schema for organisation address
        schema.update({'street_address': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_zip_code': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_place_of_business': [convert_from_extras, ignore_missing]})

        schema.update({'producer_type': [convert_from_extras, ignore_missing]})
        schema.update({'public_adminstration_organization': [convert_from_extras, ignore_missing]})

        # old schema is used to display old data if it exists
        schema.update({'homepages': [convert_from_extras, from_json_to_object, ignore_missing]})
        schema.update({'business_id': [convert_from_extras, ignore_missing]})
        schema.update({'oid': [convert_from_extras, ignore_missing]})
        schema.update({'alternative_name': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_pobox': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_country': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_unofficial_name': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_building_id': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_getting_there': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_parking': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_public_transport': [convert_from_extras, ignore_missing]})
        schema.update({'street_address_url_public_transport': [convert_from_extras, ignore_missing]})

        schema = add_translation_show_schema(schema)
        schema = add_languages_show(schema, self._localized_fields)

        return schema

    def db_to_form_schema_options(self, options):
        if not options.get('api', False):
            return self.db_to_form_schema()
        schema = ckan.logic.schema.group_form_schema()

        return schema

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
        except:
            return []

    def _get_authorized_parents(self):
        """ Returns a list of organizations under which the current user can put child organizations.

        The user is required to be an admin in the parent. If the user is a sysadmin, then the user will see all allowable parent organizations. """

        if not c.userobj.sysadmin:
            # If the user is not a sysadmin, then show only those parent organizations in which the user is an admin
            admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
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
        return {'organization_create': auth.organization_create, 'organization_update': auth.organization_update,
                'organization_public_adminstration_change': auth.organization_public_adminstration_change}

    def get_actions(self):
        return {'user_create': action_user_create, 'organization_show': action_organization_show}

    def before_map(self, map):
        organization_controller = 'ckanext.ytp.organizations.controller:YtpOrganizationController'

        with SubMapper(map, controller=organization_controller) as m:
            m.connect('organization_members', '/organization/members/{id}', action='members', ckan_icon='group')
            m.connect('/user_list', action='user_list', ckan_icon='user')
            m.connect('/admin_list', action='admin_list', ckan_icon='user')

        map.connect('/organization/new', action='new', controller='organization')
        map.connect('organization_read', '/organization/{id}', controller=organization_controller, action='read', ckan_icon='group')
        map.connect('organization_embed', '/organization/{id}/embed', controller=organization_controller, action='embed', ckan_icon='group')
        return map


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
            except:
                pass

    return key


def date_validator(value, context):
    """ Validator for date fields """
    if isinstance(value, datetime.date):
        return value
    if value == '':
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise Invalid(_('Date format incorrect'))
