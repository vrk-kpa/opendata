# -*- coding: utf-8 -*-

from ckan import plugins, model
from ckan.lib.plugins import DefaultOrganizationForm
from ckan.lib.navl import dictization_functions
from ckan.lib.navl.dictization_functions import Invalid
from ckan.common import _
from sqlalchemy import event
import ckanext.ytp.organizations.logic.action as action
from ckanext.ytp.organizations import auth
import logging
import pylons

import ckan.logic.schema
from ckan.common import c

from ckan.plugins import toolkit
import ast
import datetime


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


def _user_modified_listener(user_object):
    _configure()
    import uuid
    from ckan.lib.celery_app import celery

    celery.send_task("ckanext.ytp.organizations.default_organization", args=(user_object.id, _default_organization_name, _default_organization_title),
                     task_id=str(uuid.uuid4()))


class UserEventListener(object):
    _users = []

    def __init__(self, method):
        super(UserEventListener, self).__init__()
        event.listen(model.Session, 'after_commit', self._session_listener)
        event.listen(model.User, 'after_insert', self._user_model_listener)
        event.listen(model.User, 'after_update', self._user_model_listener)
        self.method = method

    def clear(self):
        self._users = []

    def _session_listener(self, session):
        if not self._users:
            return
        for user in self._users:
            self.method(user)
        self.clear()

    def _user_model_listener(self, target, value, initiator):
        if isinstance(initiator, model.User):
            if initiator.state == "active":
                self._users.append(initiator)
        else:
            log.warning("User listener called with non user object %s" % str(type(initiator)))


class YtpOrganizationsPlugin(plugins.SingletonPlugin, DefaultOrganizationForm):
    """ CKAN plugin to change how organizations work """
    plugins.implements(plugins.IGroupForm, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)

    def configure(self, config):
        _configure(config)
        self.events = UserEventListener(_user_modified_listener)

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
        schema.update({'HomePageUrls': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'HomePageDescriptions': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'HomePageTitles': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'HomePageAccessibilities': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'HomePageWCAGs': [ignore_missing, convert_to_list, unicode, convert_to_extras]})
        schema.update({'HomePagePlainLanguageAvailabilities': [ignore_missing, convert_to_list, unicode, convert_to_extras]})

        schema.update({'producer_type': [ignore_missing, unicode, convert_to_extras]})

        # schema for extra org info
        schema.update({'BusinessID': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'OID': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'AlternativeName': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'valid_from': [ignore_missing, date_validator, convert_to_extras]})
        schema.update({'valid_till': [ignore_missing, date_validator, convert_to_extras]})

        # schema for organisation address
        schema.update({'streetAddress': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'POBox': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'zipCode': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'PlaceOfBusiness': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'country': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'unofficialName': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'buildingId': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'gettingThere': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'parking': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'publicTransport': [ignore_missing, unicode, convert_to_extras]})
        schema.update({'UrlPublicTransport': [ignore_missing, unicode, convert_to_extras]})

        return schema

    def db_to_form_schema(self):
        schema = ckan.logic.schema.group_form_schema()
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_from_extras = toolkit.get_converter('convert_from_extras')

        # add following since they are missing from schema
        schema.update({'num_followers': [ignore_missing]})
        schema.update({'package_count': [ignore_missing]})

        # Schema for homepages
        schema.update({'HomePageUrls': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})
        schema.update({'HomePageDescriptions': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})
        schema.update({'HomePageTitles': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})
        schema.update({'HomePageAccessibilities': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})
        schema.update({'HomePageWCAGs': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})
        schema.update({'HomePagePlainLanguageAvailabilities': [convert_from_extras, convert_from_db_to_form_list, ignore_missing]})

        # schema for extra org info
        schema.update({'BusinessID': [convert_from_extras, ignore_missing]})
        schema.update({'OID': [convert_from_extras, ignore_missing]})
        schema.update({'AlternativeName': [convert_from_extras, ignore_missing]})
        schema.update({'valid_from': [convert_from_extras, ignore_missing]})
        schema.update({'valid_till': [convert_from_extras, ignore_missing]})

        # schema for organisation address
        schema.update({'streetAddress': [convert_from_extras, ignore_missing]})
        schema.update({'POBox': [convert_from_extras, ignore_missing]})
        schema.update({'zipCode': [convert_from_extras, ignore_missing]})
        schema.update({'PlaceOfBusiness': [convert_from_extras, ignore_missing]})
        schema.update({'country': [convert_from_extras, ignore_missing]})
        schema.update({'unofficialName': [convert_from_extras, ignore_missing]})
        schema.update({'buildingId': [convert_from_extras, ignore_missing]})
        schema.update({'gettingThere': [convert_from_extras, ignore_missing]})
        schema.update({'parking': [convert_from_extras, ignore_missing]})
        schema.update({'publicTransport': [convert_from_extras, ignore_missing]})
        schema.update({'UrlPublicTransport': [convert_from_extras, ignore_missing]})

        schema.update({'producer_type': [convert_from_extras, ignore_missing]})

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

    def _get_dropdown_menu_contents(self, vocabulary_name):
        """ Gets a vocabulary by name and mangles it to match data structure required by form.select """

        try:
            user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
            context = {'user': user['name']}
            vocabulary = toolkit.get_action('vocabulary_show')(context, {'id': 'ytp_organization_types'})
            tags = vocabulary.get('tags')

            menu_items = []
            for tag in sorted(tags):
                menu_items.append({'value': tag['name'], 'text': tag['display_name']})
            return menu_items
        except:
            return []

    def _get_authorized_parents(self):
        """ Returns a list of organizations under which the current user can put child organizations. The user is required to be an admin in the parent. """

        admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == c.userobj.id)

        admin_groups = []
        for admin_org in admin_in_orgs:
            if any(admin_org.group.name == non_looping_org.name for non_looping_org in c.allowable_parent_groups):
                admin_groups.append(admin_org.group)
        return admin_groups

    def get_helpers(self):
        return {'get_dropdown_menu_contents': self._get_dropdown_menu_contents, 'get_authorized_parents': self._get_authorized_parents}

    def get_auth_functions(self):
        return {'organization_create': auth.organization_create}


# From ckanext-hierarchy
class YtpOrganizationsDisplayPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)

    # IConfigurer

    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')
        plugins.toolkit.add_template_directory(config, 'public')
        plugins.toolkit.add_resource('public/scripts/vendor/jstree', 'jstree')

    # IActions

    def get_actions(self):
        return {'group_tree': action.group_tree,
                'group_tree_section': action.group_tree_section,
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
