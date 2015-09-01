from ckan import model, logic
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.common import _, c
from ckanext.ytp.request.helper import get_default_locale, get_safe_locale

import logging

log = logging.getLogger(__name__)

def member_request_cancel(context, data_dict):
    ''' Cancel own request (from logged in user). Organization_id must be provided.
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_cancel', context, data_dict)

    organization_id = data_dict.get("organization_id")
 
    query = model.Session.query(model.Member).filter(or_(model.Member.state == 'pending', model.Member.state == 'active')) \
            .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member:
        raise logic.NotFound

    return _process_request(context, member, 'cancel')


def member_request_membership_cancel(context, data_dict):
    ''' Cancel organization membership (not request) from logged in user. Organization_id must be provided.
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_membership_cancel', context, data_dict)

    organization_id = data_dict.get("organization_id")
    query = model.Session.query(model.Member).filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member:
        raise logic.NotFound

    return _process_request(context, member, 'cancel')


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

    locale = member.extras.get('locale', None) or get_default_locale()
    #_log_process(member_user, member.group.display_name, approve, admin_user)
    #mail_process_status(locale, member_user, approve, member.group.display_name, member.capacity)

    return model_dictize.member_dictize(member, context)