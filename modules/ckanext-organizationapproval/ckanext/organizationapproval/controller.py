import logging

from ckan import model
from ckan.common import request, c, _
from ckan.controllers.organization import OrganizationController
from ckan.lib import helpers as h

from ckan.lib.base import abort, render
from ckan.logic import get_action, NotFound, NotAuthorized, \
    check_access, clean_dict, tuplize_dict, parse_params, ValidationError
import ckan.lib.navl.dictization_functions as dictization_functions

log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
DataError = dictization_functions.DataError


class OrganizationApprovalController(OrganizationController):
    def manage_organizations(self):
        '''
        A ckan-admin page to list and add showcase admin users.
        '''
        log.info('im in manage organizations')
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        try:
            check_access('sysadmin', context, {})
        except NotAuthorized:
            abort(401, _('User not authorized to view page'))

        # Approving, deleting or denying organizations.
        if request.method == 'POST' and request.params['org_id']:
            org_id = request.params['org_id']
            status = request.params['approval_status']
            # NOTE: should the possible statuses come from somewhere else?
            possible_statuses = ['approved', 'pending', 'denied']
            if status in possible_statuses:
                organization = get_action('organization_show')(data_dict={'id': org_id})
                if organization['approval_status'] != status:
                    organization['approval_status'] = status
                    get_action('organization_update')(data_dict=organization)
                    h.flash_success(_("Organization was successfully updated"))
                else:
                    h.flash_error(_("Status is already set to '%s'") % status)
            else:
                h.flash_error(_("Status not allowed"))

        c.organization_data = get_action('organization_list')(context, {"all_fields": True})
        log.info(c.organization_data)

        return render('admin/manage_organizations.html')
