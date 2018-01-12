from ckan import model, logic
from ckanext.ytp_request.model import MemberRequest
from ckan.common import c
from ckanext.ytp_request.helper import get_default_locale
from ckanext.ytp_request.mail import mail_process_status

import logging
import datetime

log = logging.getLogger(__name__)


def member_request_reject(context, data_dict):
    ''' Cancel request (from admin or group editor). Member request must be provided since we need both organization/user
        Difference is that this action should be logged and showed to the user. If a user cancels herself her own request can be safely
        deleted '''
    logic.check_access('member_request_reject', context, data_dict)
    _process(context, 'reject', data_dict)


def member_request_approve(context, data_dict):
    ''' Approve request (from admin or group editor). Member request must be provided since we need both organization/user'''
    logic.check_access('member_request_approve', context, data_dict)
    _process(context, 'approve', data_dict)


def _process(context, action, data_dict):
    ''' Approve or reject member request.
    :param member request: member request id
    :type member: string
    :param approve: approve or reject request
    :type accept: boolean
    '''
    approve = action == 'approve'  # else 'reject'
    # Old table member we respect the existing states but we differentiate in
    # between cancel and rejected in our new table
    state = "active" if approve else "deleted"
    request_status = "active" if approve else "rejected"
    user = context.get("user")
    mrequest_id = data_dict.get("mrequest_id")
    role = data_dict.get("role", None)
    if not mrequest_id:
        raise logic.NotFound
    if role is not None and role is not 'admin' and role is not 'editor':
        raise logic.ValidationError("Role is not a valid value")

    member = model.Session.query(model.Member).filter(
        model.Member.id == mrequest_id).first()

    if member is None or member.group.is_organization is None:
        raise logic.NotFound
    if member.state != 'pending':
        raise logic.ValidationError(
            "Membership request was not in pending state")

    # Update existing member instance
    member.state = state
    if role:
        member.capacity = role
    revision = model.repo.new_revision()
    revision.author = user

    if approve:
        message = 'Member request approved by admin.'
    else:
        message = 'Member request rejected by log.'
    if role:
        message = message + " Role changed"
    revision.message = message

    # TODO: Move this query to a helper method since it is widely used
    # Fetch the newest member_request associated to this membership (sort by
    # last modified field)
    member_request = model.Session.query(MemberRequest).filter(
        MemberRequest.membership_id == member.id).order_by('request_date desc').limit(1).first()

    # BFW: In case of pending state overwrite it since it is no final state
    member_request.status = request_status
    member_request.handling_date = datetime.datetime.utcnow()
    member_request.handled_by = c.userobj.name
    member_request.message = message
    if role:
        member_request.role = role
    member.save()

    model.repo.commit()

    member_user = model.Session.query(model.User).get(member.table_id)
    admin_user = model.User.get(user)

    locale = member_request.language or get_default_locale()
    _log_process(member_user, member.group.display_name, approve, admin_user)
    # TODO: Do we need to set a message in the UI if mail was not sent
    # successfully?
    mail_process_status(locale, member_user, approve,
                        member.group.display_name, member.capacity)
    return True


def _log_process(member_user, member_org, approve, admin_user):
    if approve:
        log.info("Membership request of %s approved to %s by admin: %s" %
                 (member_user.fullname if member_user.fullname else member_user.name, member_org,
                  admin_user.fullname if admin_user.fullname else admin_user.name))
    else:
        log.info("Membership request of %s rejected to %s by admin: %s" %
                 (member_user.fullname if member_user.fullname else member_user.name, member_org,
                  admin_user.fullname if admin_user.fullname else admin_user.name))
