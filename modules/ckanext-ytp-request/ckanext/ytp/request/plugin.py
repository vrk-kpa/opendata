import ckan.plugins as plugins
from ckan.plugins import implements, toolkit

import logging

log = logging.getLogger(__name__)

class YtpRequestPlugin(plugins.SingletonPlugin):
    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.ITemplateHelpers, inherit=Ture)
    implements(plugins.IActions, inherit=True)
    implements(plugins.IAuthFunctions, inherit=True)

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/javascript/', 'ytp_request_js')

    #IActions
    def get_actions(self):
        from ckanext.ytp.request.logic.action import get, create, delete, update

        return {
            "request_create": create.comment_create,
            "request_cancel": delete.comment_delete,
            "request_approve": get.thread_show,
            "request_reject": update.comment_update,
            "requests_list": get.comment_show,
            "comment_count": get.comment_count
        }

    #IAuthFunctions
    def get_auth_functions(self):
        from ckanext.ytp.request.logic.auth import get, create, delete, update

        return {
            'comment_create': create.comment_create,
            'comment_update': update.comment_update,
            'comment_show': get.comment_show,
            'comment_delete': delete.comment_delete,
            "comment_count": get.comment_count
        }

    # ITemplateHelpers #
    def get_helpers(self):
        return {'list_organizations': self._list_organizations, 'request_title_and_link': self._request_title_and_link}

    # IRoutes #
    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        controller = 'ckanext.ytp.request.controller:YtpRequestController'
        m.connect("member_request_new", '/member-request/new', action='new', controller=controller)
        m.connect("member_request_list", '/member-request/list', action='list', controller=controller)
        m.connect("member_request_show", '/member-request/show/{member_id}', action='show', controller=controller)
        m.connect("member_request_reject", '/member-request/reject/{member_id}', action='reject', controller=controller)
        m.connect("member_request_approve", '/member-request/approve/{member_id}', action='approve', controller=controller)
        m.connect("member_request_process", '/member-request/process', action='process', controller=controller)
        m.connect("member_request_cancel", '/member-request/cancel/{member_id}', action='cancel', controller=controller)
        m.connect("member_request_show_organization", '/member-request/show-organization/{organization_id}', action='show_organization', controller=controller)
        m.connect("member_request_membership_cancel", '/member-request/membership-cancel/{organization_id}', action='membership_cancel', controller=controller)
        return m

    def _list_organizations(self):
        context = {'user': c.user}
        data_dict = {}
        data_dict['all_fields'] = True
        data_dict['groups'] = []
        data_dict['type'] = 'organization'
        return toolkit.get_action('organization_list')(context, data_dict)

    def _request_title_and_link(self, organization_id, organization_name):
        if not c.user or not c.userobj:
            return None, None

        if c.userobj.sysadmin:
            return _("admin"), None

        member = get_user_member(organization_id)

        if not member:
            return _('Request membership'), helpers.url_for('member_request_new', selected_organization=organization_name)

        if member.state == 'pending':
            return _('Pending for approval'), helpers.url_for('member_request_show', member_id=member.id)

        return _(member.capacity), None

