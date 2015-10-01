import logging
from ckan.common import _

log = logging.getLogger(__name__)


def comment_create(context, data_dict):
    user = context['user']
    model = context['model']

    userobj = model.User.get(user)

    if not userobj:
        log.debug("User is not logged in")
        return {'success': False, 'msg': _('You must be logged in to add a comment')}

    return {'success': True}

def add_comment_subscription(context, data_dict):
    user = context['user']
    model = context['model']

    userobj = model.User.get(user)

    if not userobj:
        return {'success': False, 'msg': _('You must be logged in to subscribe to comment notifications')}

    return {'success': True}

def add_comment_subscription_org(context, data_dict):

    # TODO: implement
    
    return {'success': True}