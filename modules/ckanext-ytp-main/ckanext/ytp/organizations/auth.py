from ckan import new_authz, model
from ckan.common import _
import ckan.logic.auth as logic_auth


def organization_create(context, data_dict):
    """ This overrides CKAN's auth function to make sure that user has permission to use a specific parent organization. """

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


def organization_update(context, data_dict):
    """ This overrides CKAN's auth function to make sure that user has permission to use a specific parent organization. """

    group = logic_auth.get_group_object(context, data_dict)
    user = context['user']

    # Check that user has admin permissions in selected parent organizations
    if data_dict and data_dict.get('groups'):

        admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == new_authz.get_user_id_for_username(user, allow_none=True))

        for parent_org in data_dict['groups']:
            if any(parent_org['name'] == admin_org.group.name for admin_org in admin_in_orgs):
                break
            else:
                return {'success': False, 'msg': _('User %s is not administrator in the selected parent organization') % user}

    authorized = new_authz.has_user_permission_for_group_or_org(group.id, user, 'update')
    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit organization %s') %
                        (user, group.id)}
    else:
        return {'success': True}
