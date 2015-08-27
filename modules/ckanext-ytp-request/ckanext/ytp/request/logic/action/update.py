from ckan import model, new_authz
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.logic import NotFound, ValidationError, check_access
from ckan.common import _, c
from ckanext.ytp.request.helper import get_organization_admins, get_ckan_admins
from ckan.lib import helpers
from pylons import config

import logging

log = logging.getLogger(__name__)

def member_request_process(context, data_dict):
    ''' Approve or reject member request.
    :param member: id of the member
    :type member: string
    :param approve: approve or reject request
    :type accpet: boolean
    '''
    check_access('member_request_process', context, data_dict)
    member = model.Session.query(model.Member).get(data_dict.get("member"))
    return _process_request(context, member, 'approve' if data_dict.get('approve') else 'reject')

def _process_request(context, member, action):
    user = context["user"]

    approve = action == 'approve'  # else 'reject' or 'cancel'

    state = "active" if approve else "deleted"

    if not member or not member.group.is_organization:
        raise NotFound

    member.state = state
    revision = model.repo.new_revision()
    revision.author = user

    if 'message' in context:
        revision.message = context['message']
    else:
        revision.message = 'Processed member request'

    member.save()
    model.repo.commit()

    member_user = model.Session.query(model.User).get(member.table_id)
    admin_user = model.User.get(user)

    locale = member.extras.get('locale', None) or _get_default_locale()
    _log_process(member_user, member.group.display_name, approve, admin_user)
    _mail_process_status(locale, member_user, approve, member.group.display_name, member.capacity)

    return model_dictize.member_dictize(member, context)