from ckan import new_authz, model
from ckan.common import _, c
from sqlalchemy.sql.expression import or_
from ckanext.ytp.request.helper import get_user_member

def member_request_membership_cancel(context, data_dict):
    if not c.userobj:
        return {'success': False}

    organization_id = data_dict.get("organization_id")
    member = _get_user_member(organization_id, 'active')

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'active':
        return {'success': True}
    return {'success': False}


def member_request_cancel(context, data_dict):
    """ Cancel request access check.
        data_dict expects member or organization_id. See `logic.member_request_cancel`.
    """

    if not c.userobj:
        return {'success': False}
    member_id = data_dict.get("member", None)
    member = None
    if not member_id:
        organization_id = data_dict.get("organization_id")
        member = get_user_member(organization_id, 'pending')
    else:
        member = model.Member.get(member_id)

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'pending':
        return {'success': True}
    return {'success': False}
