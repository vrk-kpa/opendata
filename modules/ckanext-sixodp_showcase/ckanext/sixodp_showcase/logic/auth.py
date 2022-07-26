from ckanext.showcase.logic.auth import _is_showcase_admin

import logging
log = logging.getLogger(__name__)


def get_auth_functions():
    return {
        'ckanext_sixodp_showcase_apiset_association_create': apiset_association_create,
        'ckanext_sixodp_showcase_apiset_association_delete': apiset_association_delete,
    }


def apiset_association_create(context, data_dict):
    '''Create a apiset showcase association.

       Only sysadmins or user listed as Showcase Admins can create a
       apiset/showcase association.
    '''
    return {'success': _is_showcase_admin(context)}


def apiset_association_delete(context, data_dict):
    '''Delete a apiset showcase association.

       Only sysadmins or user listed as Showcase Admins can delete a
       apiset/showcase association.
    '''
    return {'success': _is_showcase_admin(context)}
