import logging
from ckan import model, authz
from ckan.common import c, _

log = logging.getLogger(__name__)


def member_request(context, data_dict):
    """ Only allowed to sysadmins or organization admins """
    if not c.userobj:
        return {'success': False}

    if authz.is_sysadmin(c.user):
        return {'success': True}

    membership = model.Member.get(data_dict.get("mrequest_id"))
    if not membership:
        return {'success': False}

    if membership.table_name != 'user':
        return {'success': False}

    query = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == membership.group_id)
    return {'success': query.count() > 0}


def member_requests_mylist(context, data_dict):
    """ Show request access check """
    # TODO: Sysadmins dont have this functionality since it is pointless. Make
    # it at the logical level
    return _only_registered_user()


def member_requests_list(context, data_dict):
    """ Show request access check """
    return _only_registered_user()


def _only_registered_user():
    if not authz.auth_is_loggedin_user():
        return {'success': False, 'msg': _('User is not logged in')}
    return {'success': True}
