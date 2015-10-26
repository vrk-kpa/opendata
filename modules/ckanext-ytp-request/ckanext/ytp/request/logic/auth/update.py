import logging

from ckan import new_authz, model

log = logging.getLogger(__name__)


def member_request_approve(context, data_dict):
    return _check_admin_access(context, data_dict)


def member_request_reject(context, data_dict):
    return _check_admin_access(context, data_dict)


def _check_admin_access(context, data_dict):
    """ Approve access check """
    if new_authz.is_sysadmin(context['user']):
        return {'success': True}

    user = model.User.get(context['user'])
    if not user:
        return {'success': False}

    member = model.Member.get(data_dict.get("member"))
    if not member:
        return {'success': False}

    if member.table_name != 'user':
        return {'success': False}

    query = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user.id).filter(model.Member.group_id == member.group_id)

    return {'success': query.count() > 0}
