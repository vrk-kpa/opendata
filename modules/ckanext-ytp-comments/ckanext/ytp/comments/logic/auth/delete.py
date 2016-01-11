import logging
from pylons.i18n import _

import ckan.new_authz as authz
from ckan import logic
import ckanext.ytp.comments.model as comment_model


log = logging.getLogger(__name__)


def comment_delete(context, data_dict):
    model = context.get('model', None)
    user = context.get('user', None)

    if model is not None:
       userobj = model.User.get(user)
    
    # If sysadmin.
    if authz.is_sysadmin(user):
        return {'success': True}

    cid = logic.get_or_bust(data_dict, 'id')

    comment = comment_model.Comment.get(cid)
    if not comment:
        return {'success': False, 'msg': _('Comment does not exist')}

    if userobj is not None and comment.user_id is userobj.id:
        return {'success': True}
        
    return {'success': False, 'msg': _('User is not the author of the comment')}




def remove_comment_subscription(context, data_dict):
    model = context.get('model', None)
    user = context.get('user', None)

    if model is not None:
       userobj = model.User.get(user)

    if userobj:
        return {'success': True}

    return {'success': False, 'msg': _('You must be logged in to unsubscribe from comment notifications')}

