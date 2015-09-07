from ckan import logic
from ckan.lib.base import h, BaseController, render, abort, request
from ckan.plugins import toolkit
from ckan.common import c
import ckan.lib.navl.dictization_functions as dict_fns
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
        context = {'user': c.user or c.author, 'save': 'save' in request.params}
        try:
            logic.check_access('member_request_create', context)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)
        
        organizations = self._list_organizations(context)

        if context.get('save'):
          return self._save_new(context)

        #FIXME: Dont send as request parameter selected organization. kinda weird
        selected_organization = request.params.get('selected_organization', None)
        extra_vars = {'selected_organization': selected_organization,'organizations': organizations}
        data_dict = {'organization_id': selected_organization}
        c.roles = toolkit.get_action('get_available_roles')(context,data_dict)
        c.user_role = 'admin'
        c.form = render("request/new_request_form.html", extra_vars=extra_vars)
        return render("request/new.html")


    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.params))))
            data_dict['group'] = data_dict['organization']
            member = toolkit.get_action('member_request_create')(context, data_dict)
            helpers.redirect_to('organizations_index', id="newrequest", member_id=member['id'])
        except logic.NotAuthorized:
            abort(401, self.not_auth_message)
        except logic.NotFound:
            abort(404, _('Item not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except logic.ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)

    def mylist(self):
        """" Lists own members requests (possibility to cancel and view current status)"""
        context = {'user': c.user or c.author}
        try:
            my_requests = toolkit.get_action('member_requests_mylist')(context, {})
            extra_vars = {'my_requests': my_requests}
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


        