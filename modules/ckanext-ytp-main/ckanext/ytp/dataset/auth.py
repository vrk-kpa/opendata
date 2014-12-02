from ckan.common import _
import ckan.logic.auth as logic_auth
import ckan.logic.auth.update as _auth_update


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
