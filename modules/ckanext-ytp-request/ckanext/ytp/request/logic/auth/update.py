import logging

from ckan import authz, model

log = logging.getLogger(__name__)


def member_request_approve(context, data_dict):
    return _check_admin_access(context, data_dict)


def member_request_reject(context, data_dict):
    return _check_admin_access(context, data_dict)


def _check_admin_access(context, data_dict):
    """ Approve access check """
    if authz.is_sysadmin(context.get('user', None)):
        return {'success': True}

    user = model.User.get(context.get('user', None))
    if not user:
        return {'success': False}

    member = model.Member.get(data_dict.get("mrequest_id"))
    if not member:
        return {'success': False}

    if member.table_name != 'user':
        return {'success': False}

    query = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user.id).filter(model.Member.group_id == member.group_id)

    return {'success': query.count() > 0}
