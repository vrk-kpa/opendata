from ckan import model, logic
from ckanext.ytp.request.model import MemberRequest
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
    user = context.get("user")

    organization_id = data_dict.get("organization_id")
 
    query = model.Session.query(model.Member).filter(or_(model.Member.state == 'pending', model.Member.state == 'active')) \
            .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member or not member.group.is_organization:
        raise logic.NotFound

    return _process_request(context, organization_id, member)


def member_request_membership_cancel(context, data_dict):
    ''' Cancel ACTIVE organization membership (not request) from logged in user. Organization_id must be provided.
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_membership_cancel', context, data_dict)

    user = context.get("user")
    organization_id = data_dict.get("organization_id")
    query = model.Session.query(model.Member).filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member or not member.group.is_organization:
        raise logic.NotFound

    return _process_request(context, organization_id, member)

def _process_request(context, organization_id, member):
    ''' Cancel a member request or existing membership.
        Delete from database the member request and set delete state in member table
    :param member: id of the member
    :type member: string
    '''
    user = context.get("user")

    #Delete member request from table
    model.Session.query(MemberRequest).filter(MemberRequest.member_id == c.userobj.id) \
        .filter(MemberRequest.organization_id == organization_id).delete()

    #Logical delete on table member
    member.state = 'deleted'
    
    revision = model.repo.new_revision()
    revision.author = user
    revision.message = u'Member request deleted by user'

    member.save()
    model.repo.commit()

    return model_dictize.member_dictize(member, context)
