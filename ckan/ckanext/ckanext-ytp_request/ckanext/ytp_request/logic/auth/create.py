from ckanext.ytp_request.helper import get_user_member
import logging
from ckan.common import _
from flask_login import current_user
log = logging.getLogger(__name__)


def member_request_create(context, data_dict):
    """ Only allow to logged in users """
    if current_user.is_anonymous:
        return {'success': False, 'msg': _('User is not logged in')}

    organization_id = None if not data_dict else data_dict.get(
        'organization_id', None)
    if organization_id:
        member = get_user_member(organization_id)
        if member:
            return {'success': False, 'msg': _('The user has already a pending request or an active membership')}
    return {'success': True}
