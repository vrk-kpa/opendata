import logging
from math import ceil

from ckan import model
from ckan.common import request, c, _
from ckan.controllers.organization import OrganizationController
from ckan.lib import helpers as h
from ckan.lib.base import abort, render
from ckan.logic import get_action, NotAuthorized, check_access
import ckan.lib.navl.dictization_functions as dictization_functions

from logic import send_organization_approved

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
                    if status == 'approved':
                        send_organization_approved(organization)
                    h.flash_success(_("Organization was successfully updated"))
                else:
                    h.flash_error(_("Status is already set to '%s'") % status)
            else:
                h.flash_error(_("Status not allowed"))

        # NOTE: This might cause slowness, get's all organizations and they are filtered later.
        # Organization list action doesn't support sorting by any field.
        # Maybe would be better to build a custom action for this case.
        organization_list = get_action('organization_list')(context, {"all_fields": True})

        page_num = 1
        per_page = 50.0

        # Total number of pages of organizations
        total_pages = int(ceil(len(organization_list) / per_page))

        if 'page' in request.params:
            page_num = int(request.params['page'])

        # Return 20 most recently added organizations
        c.organization_data = sorted(organization_list, key=lambda x: x['created'], reverse=True)[
            (int(per_page) * (page_num - 1)):(int(per_page) * page_num)
        ]

        return render('admin/manage_organizations.html', extra_vars={
            'current_page': page_num,
            'total_pages': total_pages,
        })
