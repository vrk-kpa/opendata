from ckan import model
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.logic import NotFound, ValidationError, check_access
from ckan.common import _, c
from ckanext.ytp.request.helper import get_default_locale
from ckan.lib import helpers
from pylons import config

import logging

log = logging.getLogger(__name__)

def member_request_reject(context, data_dict):
    ''' Cancel request (from admin or group editor). Member request must be provided since we need both organization/user
        Difference is that this action should be logged and showed to the user. If a user cancels herself her own request can be safely
        deleted '''
    logic.check_access('member_request_reject', context, data_dict)
    _process(context,'approve',data_dict)

def member_request_approve(context, data_dict):
    ''' Approve request (from admin or group editor). Member request must be provided since we need both organization/user'''
    logic.check_access('member_request_approve', context, data_dict)
    _process(context,'reject',data_dict)


def _process(context, action, data_dict):
    ''' Approve or reject member request.
    :param member request: member request id
    :type member: string
    :param approve: approve or reject request
    :type accept: boolean
    '''
    approve = action == 'approve'  # else 'reject'
    state = "active" if approve else "deleted"
    user = context.get("user")

    member_request = model.Session.query(MemberRequest).get(data_dict.get("mrequest_id"))
    member = model.Session.query(model.Member).filter(model.Member.table_id == member_request.member_id).filter(model.Member.group.id == member_request.organization.id).first()

    if not member or not member.group.is_organization:
        raise NotFound
    if member.state != 'pending':
        #TODO: throw better exception
        raise logic.NotFound

    member.state = state
    revision = model.repo.new_revision()
    revision.author = user

    if approve:
        message = 'Member request approved by admin'
    else:
        message = 'Member request rejected by admin'
    
    revision.message = message

    member_request.status = state
    member_request.handling_date = datetime.datetime.now
    
    member.save()
    member_request.save()
    model.repo.commit()

    member_user = model.Session.query(model.User).get(member.table_id)
    admin_user = model.User.get(user)

    #locale = member_request.language or get_default_locale()
    _log_process(member_user, member.group.display_name, approve, admin_user)
    #_mail_process_status(locale, member_user, approve, member.group.display_name, member.capacity)

    return model_dictize.member_dictize(member, context)


def _log_process(member_user, member_org, approve, admin_user):
    if approve:
        log.info("Membership request of %s approved to %s by admin: %s" %
                 (member_user.fullname if member_user.fullname else member_user.name, member_org,
                  admin_user.fullname if admin_user.fullname else admin_user.name))
    else:
        log.info("Membership request of %s rejected to %s by admin: %s" %
                 (member_user.fullname if member_user.fullname else member_user.name, member_org,
                  admin_user.fullname if admin_user.fullname else admin_user.name))