from ckan import new_authz, model
from ckan.common import _, c
from sqlalchemy.sql.expression import or_

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