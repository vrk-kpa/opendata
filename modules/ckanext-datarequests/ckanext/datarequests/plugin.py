# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of CKAN Data Requests Extension.

# CKAN Data Requests Extension is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# CKAN Data Requests Extension is distributed in the hope that it will be useful# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with CKAN Data Requests Extension. If not, see <http://www.gnu.org/licenses/>.

import ckan.plugins as p
from ckan.common import c
from ckan import model
import auth
import actions
import constants
import ckan.plugins.toolkit as tk

from pylons import config

def get_config_bool_value(config_name, default_value=False):
    value = config.get(config_name, default_value)
    value = value if type(value) == bool else value != 'False'
    return value



class DataRequestsPlugin(p.SingletonPlugin):

    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IConfigurer)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.ITemplateHelpers)

    def __init__(self, name=None):
        self.comments_enabled = get_config_bool_value('ckan.datarequests.comments', True)

    ######################################################################
    ############################## IACTIONS ##############################
    ######################################################################

    def get_actions(self):
        additional_actions = {
            constants.DATAREQUEST_CREATE: actions.datarequest_create,
            constants.DATAREQUEST_SHOW: actions.datarequest_show,
            constants.DATAREQUEST_UPDATE: actions.datarequest_update,
            constants.DATAREQUEST_INDEX: actions.datarequest_index,
            constants.DATAREQUEST_DELETE: actions.datarequest_delete,
            constants.DATAREQUEST_CLOSE: actions.datarequest_close
        }

        if self.comments_enabled:
            additional_actions[constants.DATAREQUEST_COMMENT] = actions.datarequest_comment
            additional_actions[constants.DATAREQUEST_COMMENT_LIST] = actions.datarequest_comment_list
            additional_actions[constants.DATAREQUEST_COMMENT_SHOW] = actions.datarequest_comment_show
            additional_actions[constants.DATAREQUEST_COMMENT_UPDATE] = actions.datarequest_comment_update
            additional_actions[constants.DATAREQUEST_COMMENT_DELETE] = actions.datarequest_comment_delete

        return additional_actions

    ######################################################################
    ########################### AUTH FUNCTIONS ###########################
    ######################################################################

    def get_auth_functions(self):
        auth_functions = {
            constants.DATAREQUEST_CREATE: auth.datarequest_create,
            constants.DATAREQUEST_SHOW: auth.datarequest_show,
            constants.DATAREQUEST_UPDATE: auth.datarequest_update,
            constants.DATAREQUEST_INDEX: auth.datarequest_index,
            constants.DATAREQUEST_DELETE: auth.datarequest_delete,
            constants.DATAREQUEST_CLOSE: auth.datarequest_close,
        }

        if self.comments_enabled:
            auth_functions[constants.DATAREQUEST_COMMENT] = auth.datarequest_comment
            auth_functions[constants.DATAREQUEST_COMMENT_LIST] = auth.datarequest_comment_list
            auth_functions[constants.DATAREQUEST_COMMENT_SHOW] = auth.datarequest_comment_show
            auth_functions[constants.DATAREQUEST_COMMENT_UPDATE] = auth.datarequest_comment_update
            auth_functions[constants.DATAREQUEST_COMMENT_DELETE] = auth.datarequest_comment_delete

        return auth_functions

    ######################################################################
    ############################ ICONFIGURER #############################
    ######################################################################

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

        # Register this plugin's fanstatic directory with CKAN.
        tk.add_public_directory(config, 'public')

        # Register this plugin's fanstatic directory with CKAN.
        tk.add_resource('fanstatic', 'datarequest')

    ######################################################################
    ############################## IROUTES ###############################
    ######################################################################

    def before_map(self, m):
        # Data Requests index
        m.connect('datarequests_index', "/%s" % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='index', conditions=dict(method=['GET']))

        # Create a Data Request
        m.connect('/%s/new' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='new', conditions=dict(method=['GET', 'POST']))

        # Show a Data Request
        m.connect('datarequest_show', '/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='show', conditions=dict(method=['GET']), ckan_icon='question-sign')

        # Update a Data Request
        m.connect('/%s/edit/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='update', conditions=dict(method=['GET', 'POST']))

        # Delete a Data Request
        m.connect('/%s/delete/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='delete', conditions=dict(method=['POST']))

        # Close a Data Request
        m.connect('/%s/close/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='close', conditions=dict(method=['GET', 'POST']))

        # Data Request that belongs to an organization
        m.connect('organization_datarequests', '/organization/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='organization_datarequests', conditions=dict(method=['GET']),
                  ckan_icon='question-sign')

        # Data Request that belongs to an user
        m.connect('user_datarequests', '/user/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='user_datarequests', conditions=dict(method=['GET']),
                  ckan_icon='question-sign')

        if self.comments_enabled:
            # Comment, update and view comments (of) a Data Request
            m.connect('datarequest_comment', '/%s/comment/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                      action='comment', conditions=dict(method=['GET', 'POST']), ckan_icon='comment')

            # Delete data request
            m.connect('/%s/comment/{datarequest_id}/delete/{comment_id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                      action='delete_comment', conditions=dict(method=['GET', 'POST']))

        return m

    ######################################################################
    ######################### ITEMPLATESHELPER ###########################
    ######################################################################

    def get_helpers(self):
        return {
            'show_comments_tab': lambda: self.comments_enabled,
            'is_organization_requestable': self.has_organization_maintainer,
            'active_organizations_available': self.active_organizations_available
        }

    def active_organizations_available(self, permission='edit_group'):
        '''Return a list of organizations that the current user has the specified
        permission for and have an active maintainer.
        '''
        context = {'user': c.user}
        data_dict = {'permission': permission}
        organizations = tk.get_action('organization_list_for_user')(context, data_dict)
        return [organization for organization in organizations if self.has_organization_maintainer(organization['id'])]

    def has_organization_maintainer(self, orgid):
        '''Returns true if the given organization has admin or maintainer role associated to it other than the default admin
           false otherwise'''
        context = {'user': c.user}
        data_dict={'id': orgid, 'capacity': 'admin'}

        ## TODO: Do it in a more python way
        members = tk.get_action('member_list')(context,data_dict)

        if members:
            sys_maintainers = 0
            ## Return all sysadmins and check whether this organization has any other admin more than a default sysadmin has it
            admins = list(model.Session.query(model.User).filter(model.User.sysadmin == True))  # noqa
            adminsuuid = {}
            for admin in admins:
                adminsuuid['%s' %admin.id] = []

            for member in members:
                if any(str(member[0]) in adminuuid for adminuuid in adminsuuid):
                    sys_maintainers += 1
            return sys_maintainers != len(members)
        else:
            return False

