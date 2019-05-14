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
        if request.method == 'POST' and request.params['organization_id']:
            organization_id = request.params['organization_id']
            action_type = request.params['action_type']
            try:
                # TODO: update this to do the correct action
                get_action('ckanext_showcase_admin_add')(data_dict={'username': 'username'})
            except NotAuthorized:
                abort(401, _('Unauthorized to perform that action'))
            except NotFound:
                h.flash_error(_("Organization '{org_id}' not found.").format(
                    org_id=organization_id))
            except ValidationError as e:
                h.flash_notice(e.error_summary)
            else:
                h.flash_success(_("The organization has been deleted"))

            return redirect(h.url_for(
                controller='ckanext.ytp_main.controller:YtpOrganizationController',
                action='manage_organizations'))

        c.organization_data = get_action('organization_list')(context, {"all_fields": True})
        log.info(c.organization_data)

        return render('admin/manage_organizations.html')
