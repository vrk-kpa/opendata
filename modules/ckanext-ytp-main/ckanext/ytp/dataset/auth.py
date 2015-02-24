from ckan.common import _
import ckan.logic.auth as logic_auth
import ckan.logic.auth.update as _auth_update
from ckan.logic import get_action, check_access, NotAuthorized


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
