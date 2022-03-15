import ckan.plugins as plugins
from ckan.plugins import implements, toolkit
from ckan.lib.plugins import DefaultTranslation
import logging
from .cli import get_commands
from . import views

log = logging.getLogger(__name__)


class YtpRequestPlugin(plugins.SingletonPlugin, DefaultTranslation):
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IActions, inherit=True)
    implements(plugins.IAuthFunctions, inherit=True)
    implements(plugins.ITranslation)
    implements(plugins.IClick)
    implements(plugins.IBlueprint)

    # IConfigurer #
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('public', 'request_js')

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
            "member_request_show": get.member_request,
            "organization_list_without_memberships": get.organization_list_without_memberships
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
            "member_request_show": get.member_request,
            "organization_list_without_memberships": get.organization_list_without_memberships
        }

    # IClick
    def get_commands(self):
        return get_commands()

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprint()
