import logging
from ckan import new_authz

log = logging.getLogger(__name__)

def member_requests_list(context, data_dict):
	""" Show request access check """
    return _only_registered_user()

def member_request_show(context, data_dict):
    """ Show request access check """
    return _only_registered_user()

def _only_registered_user():
    if not new_authz.auth_is_loggedin_user():
        return {'success': False, 'msg': _('User is not logged in')}
    return {'success': True}