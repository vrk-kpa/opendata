from ckan import new_authz, model
from ckan.common import _


def organization_create(context, data_dict):
    """ This overrides CKAN's auth function to make sure that user has permission to use a specific parent org. """

    user = context['user']
    user = new_authz.get_user_id_for_username(user, allow_none=True)

    # Check that user has admin permissions in selected parent organizations
    if data_dict and data_dict.get('groups'):

        admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user)

        for group in data_dict['groups']:
            if any(group['name'] == admin_org.group.name for admin_org in admin_in_orgs):
                break
            else:
                return {'success': False, 'msg': _('User %s is not administrator in the selected parent organization') % user}

    if user and new_authz.check_config_permission('user_create_organizations'):
        return {'success': True}
    return {'success': False,
            'msg': _('User %s not authorized to create organizations') % user}
