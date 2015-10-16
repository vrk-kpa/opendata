from ckan import model, logic
from ckanext.ytp.request.model import MemberRequest
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.common import _, c
from ckanext.ytp.request.helper import get_default_locale, get_safe_locale

import logging

log = logging.getLogger(__name__)


def member_request_cancel(context, data_dict):
    ''' Cancel PENDING own request (from logged in user). Organization_id must be provided.
    :param organization_id: id of the organization
    :type member: string
    '''
    logic.check_access('member_request_cancel', context, data_dict)
    user = context.get("user")

    organization_id = data_dict.get("organization_id")
 
    query = model.Session.query(model.Member).filter(model.Member.state == 'pending') \
            .filter(model.Member.table_name == 'user').filter(model.Member.table_id == c.userobj.id).filter(model.Member.group_id == organization_id)
    member = query.first()

    if not member or not member.group.is_organization:
        raise logic.NotFound

    return _process_request(context, member)


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

    return _process_request(context, member)

def _process_request(context, member):
    ''' Cancel a member request or existing membership.
    :param member: id of the member
    :type member: string
    '''
    user = context.get("user")

    #pending is not end state. End states are active, cancel, or reject for MemberRequest. Only 1 pending is allowed at most
    query = model.Session.query(MemberRequest).filter(MemberRequest.membership_id == member.id).order_by('request_date desc').limit(1)
    
    member_request = query.first()
    #Logical delete on table member
    member.state = 'deleted'
    
    #TODO: If pending modify state to cancel, If active create a new one? Handled by 'user' handling_date  
    revision = model.repo.new_revision()
    revision.author = user
    revision.message = u'Member request cancelled by user'

    member.save()
    model.repo.commit()

    return model_dictize.member_dictize(member, context)
