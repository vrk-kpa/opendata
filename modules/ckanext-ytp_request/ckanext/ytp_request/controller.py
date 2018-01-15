from ckan import logic, model
from ckan.lib import helpers
from ckan.lib.base import BaseController, render, abort, request
from ckan.plugins import toolkit
from ckan.common import c, _
import ckan.lib.navl.dictization_functions as dict_fns
import logging

log = logging.getLogger(__name__)


class YtpRequestController(BaseController):

    not_auth_message = _('Unauthorized')
    request_not_found_message = _('Request not found')

    def _list_organizations(context, errors=None, error_summary=None):
        data_dict = {}
        data_dict['all_fields'] = True
        data_dict['groups'] = []
        data_dict['type'] = 'organization'
        # TODO: Filter our organizations where the user is already a member or
        # has a pending request
        return toolkit.get_action('organization_list')({}, data_dict)

    def new(self, errors=None, error_summary=None):
        context = {'user': c.user or c.author,
                   'save': 'save' in request.params}
        try:
            logic.check_access('member_request_create', context)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)

        organizations = self._list_organizations(context)

        if context.get('save') and not errors:
            return self._save_new(context)

        # FIXME: Don't send as request parameter selected organization. kinda
        # weird
        selected_organization = request.params.get(
            'selected_organization', None)
        extra_vars = {'selected_organization': selected_organization, 'organizations': organizations,
                      'errors': errors or {}, 'error_summary': error_summary or {}}
        c.roles = self._get_available_roles(context, selected_organization)
        c.user_role = 'admin'
        c.form = render("request/new_request_form.html", extra_vars=extra_vars)
        return render("request/new.html")

    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(dict_fns.unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            data_dict['group'] = data_dict['organization']
            # TODO: Do we need info message at the UI level when e-mail could
            # not be sent?
            member = toolkit.get_action(
                'member_request_create')(context, data_dict)
            helpers.redirect_to('organizations_index',
                                id="newrequest", membership_id=member['id'])
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except logic.NotFound:
            abort(404, _('Item not found'))
        except logic.NotAuthorized:
            abort(405, self.not_auth_message)
        except logic.ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(errors, error_summary)

    def show(self, mrequest_id):
        """" Shows a single member request. To be used by admins in case they want to modify granted role or accept via e-mail """
        context = {'user': c.user or c.author}
        try:
            membershipdto = toolkit.get_action('member_request_show')(
                context, {'mrequest_id': mrequest_id})
            member_user = model.Session.query(
                model.User).get(membershipdto['user_id'])
            context = {'user': member_user.name}
            roles = self._get_available_roles(
                context, membershipdto['organization_name'])
            extra_vars = {"membership": membershipdto,
                          "member_user": member_user, "roles": roles}
            return render('request/show.html', extra_vars=extra_vars)
        except logic.NotFound:
            abort(404, self.request_not_found_message)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)

    def mylist(self):
        """" Lists own members requests (possibility to cancel and view current status)"""
        context = {'user': c.user or c.author}
        id = request.params.get('id', None)
        try:
            my_requests = toolkit.get_action(
                'member_requests_mylist')(context, {})
            message = None
            if id:
                message = _("Member request processed successfully")
            extra_vars = {'my_requests': my_requests, 'message': message}
            return render('request/mylist.html', extra_vars=extra_vars)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)

    def list(self):
        """ Lists member requests to be approved by admins"""
        context = {'user': c.user or c.author}
        id = request.params.get('id', None)
        try:
            member_requests = toolkit.get_action(
                'member_requests_list')(context, {})
            message = None
            if id:
                message = _("Member request processed successfully")
            log.debug("%s", message)
            extra_vars = {
                'member_requests': member_requests, 'message': message}
            return render('request/list.html', extra_vars=extra_vars)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)

    def cancel(self):
        """ Logged in user can cancel pending requests not approved yet by admins/editors"""
        context = {'user': c.user or c.author}
        organization_id = request.params.get('organization_id', None)
        try:
            toolkit.get_action('member_request_cancel')(
                context, {"organization_id": organization_id})
            id = 'cancel'
            helpers.redirect_to('member_requests_mylist', id=id)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)
        except logic.NotFound:
            abort(404, self.request_not_found_message)

    def reject(self, mrequest_id):
        """ Controller to reject member request (only admins or group editors can do that """
        return self._processbyadmin(mrequest_id, False)

    def approve(self, mrequest_id):
        """ Controller to approve member request (only admins or group editors can do that) """
        return self._processbyadmin(mrequest_id, True)

    def membership_cancel(self, organization_id):
        """ Logged in user can cancel already approved/existing memberships """
        context = {'user': c.user or c.author}
        try:
            toolkit.get_action('member_request_membership_cancel')(
                context, {"organization_id": organization_id})
            id = 'cancel'
            helpers.redirect_to('member_requests_mylist', id=id)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)
        except logic.NotFound:
            abort(404, self.request_not_found_message)

    def _get_available_roles(self, context, organization_id):
        data_dict = {'organization_id': organization_id}
        return toolkit.get_action('get_available_roles')(context, data_dict)

    def _processbyadmin(self, mrequest_id, approve):
        context = {'user': c.user or c.author}
        role = request.params.get('role', None)
        data_dict = {"mrequest_id": mrequest_id, 'role': role}
        try:
            if approve:
                toolkit.get_action('member_request_approve')(
                    context, data_dict)
                id = 'approved'
            else:
                toolkit.get_action('member_request_reject')(context, data_dict)
                id = 'rejected'
            helpers.redirect_to("member_requests_list", id=id)
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)
        except logic.NotFound:
            abort(404, self.request_not_found_message)
        except logic.ValidationError as e:
            abort(400, str(e))
