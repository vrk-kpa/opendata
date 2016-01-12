import logging
from ckan.common import _

log = logging.getLogger(__name__)

def comment_create(context, data_dict):
    user = context.get('user', None)
    model = context.get('model', None)

    if model is not None:
        userobj = model.User.get(user)
        
    if userobj:
        return {'success': True}

    log.debug("User is not logged in")
    return {'success': False, 'msg': _('You must be logged in to add a comment')}


def add_comment_subscription(context, data_dict):
    user = context.get('user', None)
    model = context.get('model', None)

    if model is not None:
        userobj = model.User.get(user)

    if userobj:
        return {'success': True}

    return {'success': False, 'msg': _('You must be logged in to subscribe to comment notifications')}
