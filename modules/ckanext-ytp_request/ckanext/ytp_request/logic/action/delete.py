from ckan import model, logic
from ckanext.ytp_request.model import MemberRequest
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.common import c
from sqlalchemy.sql import func
from ckanext.ytp_request.helper import get_safe_locale

import logging

log = logging.getLogger(__name__)


def member_request_cancel(context, data_dict):
    ''' Cancel own request (from logged in user). Organization_id must be provided.
     We cannot rely on membership_id since existing memberships can be created also from different ways (e.g. a user creates an organization)
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_cancel', context, data_dict)

    organization_id = data_dict.get("organization_id")

    query = model.Session.query(model.Member).filter(or_(model.Member.state == 'pending', model.Member.state == 'active')) \
        .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member or not member.group.is_organization:
        raise logic.NotFound

    return _process_request(context, organization_id, member, 'pending')


def member_request_membership_cancel(context, data_dict):
    ''' Cancel ACTIVE organization membership (not request) from logged in user. Organization_id must be provided.
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_membership_cancel', context, data_dict)

    organization_id = data_dict.get("organization_id")
    query = model.Session.query(model.Member).filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member or not member.group.is_organization:
        raise logic.NotFound

    return _process_request(context, organization_id, member, 'active')


def _process_request(context, organization_id, member, status):
    ''' Cancel a member request or existing membership.
        Delete from database the member request (if existing) and set delete state in member table
    :param member: id of the member
    :type member: string
    '''
    user = context.get("user")

    # Logical delete on table member
    member.state = 'deleted'
    # Fetch the newest member_request associated to this membership (sort by
    # last modified field)
    member_request = model.Session.query(MemberRequest).filter(
        MemberRequest.membership_id == member.id).order_by('request_date desc').limit(1).first()

    # BFW: Create a new instance every time membership status is changed
    message = u'MemberRequest cancelled by own user'
    locale = get_safe_locale()
    mrequest_date = func.now()
    if member_request is not None and member_request.status == status:
        locale = member_request.language
        mrequest_date = member_request.request_date

    member_request = MemberRequest(membership_id=member.id, role=member.capacity, status="cancel", request_date=mrequest_date,
                                   language=locale, handling_date=func.now(), handled_by=c.userobj.name, message=message)
    model.Session.add(member_request)

    revision = model.repo.new_revision()
    revision.author = user
    revision.message = u'Member request deleted by user'

    member.save()
    model.repo.commit()

    return model_dictize.member_dictize(member, context)
