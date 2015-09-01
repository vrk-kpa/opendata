from ckan import logic
from ckan.lib.base import h, BaseController, render, abort, request
from ckan.plugins import toolkit
from ckan.common import c

import logging

log = logging.getLogger(__name__)

class YtpRequestController(BaseController):

    def _list_organizations(self,context):
        data_dict = {}
        data_dict['all_fields'] = True
        data_dict['groups'] = []
        data_dict['type'] = 'organization'
        return toolkit.get_action('organization_list')(context,data_dict)

    def new(self):
        context = {'user': c.user or c.author}
        try:
            logic.check_access('member_request_create', context)
            organizations = self._list_organizations(context)
            #FIXME: Dont send as request parameter selected organization. kinda weird
            extra_vars = {'selected_organization': request.params.get('selected_organization', None),'organizations': organizations}
            c.roles = self._get_available_roles()
            c.form = render("request/new_request_form.html", extra_vars=extra_vars)
            return render("request/new.html")
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)


    def mylist(self):
        """" Lists own members requests (possibility to cancel and view current status)"""
        context = {'user': c.user or c.author}
        try:
            own_requests = toolkit.get_action('member_requests_mylist')(context, {})
            extra_vars = {'own_requests': own_requests}
            return render('request/mylist.html', extra_vars=extra_vars)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message) 

    
    def list(self):
        """ Lists member requests to be approved by admins"""
        context = {'user': c.user or c.author}
        try:
            member_requests = toolkit.get_action('member_requests_list')(context, {})
            extra_vars = {'member_requests': member_requests}
            return render('request/list.html', extra_vars=extra_vars)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)

    def cancel(self, organization_id):
        """ Logged in user can cancel pending requests not approved yet by admins/editors"""
        context = {'user': c.user or c.author}
        try:
            toolkit.get_action('member_request_cancel')(context,{"organization_id": organization_id})
            helpers.redirect_to('organizations_index')
        except NotAuthorized:
            abort(401, self.not_auth_message)
        except NotFound:
            abort(404,_('Request not found'))


    def membership_cancel(self, organization_id):
        """ Logged in user can cancel already approved/existing memberships """
        context = {'user': c.user or c.author}
        try:
            toolkit.get_action('member_request_membership_cancel')(context, {"organization_id": organization_id})
            helpers.redirect_to('organizations_index')
        except NotAuthorized:
            abort(401, self.not_auth_message)
        except NotFound:
            abort(404, _('Request not found'))

    def _get_available_roles(self, user=None, context=None):
        roles = []
        for role in toolkit.get_action('member_roles_list')(context, {}):
            if role['value'] != 'member':
                roles.append(role)
        return roles