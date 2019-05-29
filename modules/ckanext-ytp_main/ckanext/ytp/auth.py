from ckan import model
from ckan.common import _, c
import ckan.logic.auth as logic_auth
import ckan.logic.auth.update as _auth_update
from ckan.logic import get_action, check_access, NotAuthorized
import ckan.authz as authz

import logging
log = logging.getLogger(__name__)


def related_update(context, data_dict):
    model = context['model']
    user = context['user']
    if not user:
        return {'success': False,
                'msg': _('Only the owner can update a related item')}

    related = logic_auth.get_related_object(context, data_dict)
    userobj = model.User.get(user)

    if related.datasets:
        package = related.datasets[0]
        pkg_dict = {'id': package.id}
        authorized = _auth_update.package_update(context, pkg_dict).get('success')
        if authorized:
            return {'success': True}

    if not userobj or userobj.id != related.owner_id:
        return {'success': False,
                'msg': _('Only the owner can update a related item')}

    # Only sysadmins can change the featured field.
    if ('featured' in data_dict and data_dict['featured'] != related.featured):
        return {'success': False,
                'msg': _('You must be a sysadmin to change a related item\'s '
                         'featured field.')}

    return {'success': True}


def related_create(context, data_dict):
    '''Users must be logged-in to create related items.
    To create a featured item the user must be a sysadmin.
    '''
    model = context['model']
    user = context['user']
    userobj = model.User.get(user)

    if userobj:
        if data_dict.get('featured', 0) != 0:
            return {'success': False,
                    'msg': _('You must be a sysadmin to create a featured related item')}
        if data_dict.get('dataset_id', None) is not None:
            dataset = get_action('package_show')(context, {'id': data_dict['dataset_id']})
            if dataset.get('collection_type', None) == 'Interoperability Tools':
                try:
                    check_access('package_update', context, {'id': data_dict['dataset_id']})
                    return {'success': True}
                except NotAuthorized:
                    return {'success': False, 'msg': _('You must be logged in to add a related item')}
        return {'success': True}

    return {'success': False, 'msg': _('You must be logged in to add a related item')}


def _check_public_adminstration_flag(context, data_dict):
    public_adminstration_organization = (data_dict.get(
        'public_adminstration_organization', None) if data_dict else None) == 'true'
    if public_adminstration_organization and not c.userobj.sysadmin:
        return {'success': False, 'msg': _('User %s not authorized to create public organizations') % context['user']}
    return None


def organization_public_adminstration_change(context, data_dict):
    return {'success': False, 'msg': _('User %s not authorized to create public organizations') % context['user']}


def public_organization_create(context, data_dict):
    if not c.userobj or not c.userobj.sysadmin:
        return {'success': False}
    return {'success': True}


def organization_create(context, data_dict):
    """ This overrides CKAN's auth function to make sure that user has permission to use a specific parent organization. """

    if not c.userobj:
        return {'success': False, 'msg': _('Only registered users can create organizations')}

    # Check that user has admin permissions in selected parent organizations
    if data_dict and data_dict.get('groups'):

        admin_in_orgs = (model.Session.query(model.Member).filter(model.Member.state == 'active')
                                                          .filter(model.Member.table_name == 'user')
                                                          .filter(model.Member.capacity == 'admin')
                                                          .filter(model.Member.table_id == c.userobj.id))

        for group in data_dict['groups']:
            if any(group['name'] == admin_org.group.name for admin_org in admin_in_orgs):
                break
            else:
                return {'success': False,
                        'msg': _('User %s is not administrator in the selected parent organization') % context['user']}

    check = _check_public_adminstration_flag(context, data_dict)
    if check:
        return check

    if authz.check_config_permission('user_create_organizations'):
        return {'success': True}
    return {'success': False,
            'msg': _('User %s not authorized to create organizations') % context['user']}


def package_update(context, data_dict):
    """Overrides CKAN auth function to support personal datasets setting in organizations"""

    result = _auth_update.package_update(context, data_dict)

    if result['success']:
        user = logic_auth.get_user_object(context, {'id': context.get('user')})
        package = logic_auth.get_package_object(context, data_dict)

        # Showcases don't have organizations
        if package.type != "showcase":
            org = logic_auth.get_group_object(context, {'id': package.owner_org})

            personal_datasets = 'personal_datasets' in org.extras.get('features', [])
            if personal_datasets and package.creator_user_id != user.id:
                result = {
                    'success': False,
                    'msg': _('Cannot modify dataset because of organization policy')
                }

    return result


def user_list(context, data_dict):
    if not context.userobj or not context.userobj.sysadmin:
        return {'success': False, 'msg': _('Only system administrators are allowed to view user list.')}
    return {'success': True}
