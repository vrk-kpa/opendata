import ckan.plugins as plugins
from ckan.plugins import implements, toolkit
import logging

log = logging.getLogger(__name__)


class YtpRequestPlugin(plugins.SingletonPlugin):
    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IActions, inherit=True)
    implements(plugins.IAuthFunctions, inherit=True)

    # IConfigurer #
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/javascript/', 'request_js')

    # IActions
    def get_actions(self):
        from ckanext.ytp_request.logic.action import get, create, update, delete

        return {
            "member_request_create": create.member_request_create,
            "member_request_cancel": delete.member_request_cancel,
            "member_request_reject": update.member_request_reject,
            "member_request_approve": update.member_request_approve,
            "member_request_membership_cancel": delete.member_request_membership_cancel,
            "member_requests_list": get.member_requests_list,
            "member_requests_mylist": get.member_requests_mylist,
            "get_available_roles": get.get_available_roles,
            "member_request_show": get.member_request
        }

    # IAuthFunctions
    def get_auth_functions(self):
        from ckanext.ytp_request.logic.auth import get, create, update, delete

        return {
            "member_request_create": create.member_request_create,
            "member_request_cancel": delete.member_request_cancel,
            "member_request_reject": update.member_request_reject,
            "member_request_approve": update.member_request_approve,
            "member_request_membership_cancel": delete.member_request_membership_cancel,
            "member_requests_list": get.member_requests_list,
            "member_requests_mylist": get.member_requests_mylist,
            "member_request_show": get.member_request
        }

    # IRoutes #
    def before_map(self, m):
        """ CKAN autocomplete discards vocabulary_id from request. Create own api for this. """
        controller = 'ckanext.ytp_request.controller:YtpRequestController'
        m.connect('member_request_create', '/member-request/new',
                  action='new', controller=controller)
        m.connect('member_requests_mylist', '/member-request/mylist',
                  action='mylist', controller=controller)
        m.connect('member_requests_list', '/member-request/list',
                  action='list', controller=controller)
        m.connect('member_request_reject',
                  '/member-request/reject/{mrequest_id}', action='reject', controller=controller)
        m.connect('member_request_approve',
                  '/member-request/approve/{mrequest_id}', action='approve', controller=controller)
        m.connect('member_request_cancel', '/member-request/cancel',
                  action='cancel', controller=controller)
        m.connect('member_request_membership_cancel',
                  '/member-request/membership-cancel/{organization_id}', action='membership_cancel', controller=controller),
        m.connect('member_request_show',
                  '/member-request/{mrequest_id}', action='show', controller=controller)
        return m
