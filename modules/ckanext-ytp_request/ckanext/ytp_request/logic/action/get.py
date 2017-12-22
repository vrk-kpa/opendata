from ckan import logic, model
from ckan.common import _
from ckan.lib.dictization import model_dictize
from ckanext.ytp_request.model import MemberRequest
from ckanext.ytp_request.helper import get_organization_admins

import logging
import ckan.authz as authz

log = logging.getLogger(__name__)


def member_request(context, data_dict):
    logic.check_access('member_request_show', context, data_dict)
    mrequest_id = data_dict.get('mrequest_id', None)

    membership = model.Session.query(model.Member).get(mrequest_id)
    if not membership or membership.state != 'pending':
        raise logic.NotFound("Member request not found")

    # Return most current instance from memberrequest table
    member_request = model.Session.query(MemberRequest).filter(
        MemberRequest.membership_id == mrequest_id).order_by('request_date desc').limit(1).first()
    if not member_request or member_request.status != 'pending':
        raise logic.NotFound(
            "Member request associated with membership not found")

    member_dict = {}
    member_dict['id'] = mrequest_id
    member_dict['organization_name'] = membership.group.name
    member_dict['group_id'] = membership.group_id
    member_dict['role'] = member_request.role
    member_dict['state'] = 'pending'
    member_dict['request_date'] = member_request.request_date.strftime(
        "%d - %b - %Y")
    member_dict['user_id'] = membership.table_id
    return member_dict


def member_requests_mylist(context, data_dict):
    ''' Users wil see a list of her member requests
    '''
    logic.check_access('member_requests_mylist', context, data_dict)

    user = context.get('user', None)
    if authz.is_sysadmin(user):
        raise logic.ValidationError({}, {_("Role"): _(
            "As a sysadmin, you already have access to all organizations")})

    user_object = model.User.get(user)
    # Return current state for memberships for all organizations for the user
    # in context. (last modified date)
    membership_requests = model.Session.query(model.Member).filter(
        model.Member.table_id == user_object.id).all()
    return _membeship_request_list_dictize(membership_requests, context)


def member_requests_list(context, data_dict):
    ''' Organization admins/editors will see a list of member requests to be approved.
    :param group: name of the group (optional)
    :type group: string
    '''
    logic.check_access('member_requests_list', context, data_dict)

    user = context.get('user', None)
    user_object = model.User.get(user)
    is_sysadmin = authz.is_sysadmin(user)

    # ALL members with pending state only
    query = model.Session.query(model.Member).filter(
        model.Member.table_name == "user").filter(model.Member.state == 'pending')

    if not is_sysadmin:
        admin_in_groups = model.Session.query(model.Member).filter(model.Member.state == "active").filter(model.Member.table_name == "user") \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user_object.id)

        if admin_in_groups.count() <= 0:
            return []
        # members requests for this organization
        query = query.filter(model.Member.group_id.in_(
            admin_in_groups.values(model.Member.group_id)))

    group = data_dict.get('group', None)
    if group:
        group_object = model.Group.get(group)
        if group_object:
            query = query.filter(model.Member.group_id == group_object.id)

    members = query.all()

    return _member_list_dictize(members, context)


@logic.side_effect_free
def get_available_roles(context, data_dict=None):
    roles = logic.get_action("member_roles_list")(context, {})

    # Remove member role from the list
    roles = [role for role in roles if role['value'] != 'member']

    # If organization has no associated admin, then role editor is not
    # available
    organization_id = logic.get_or_bust(data_dict, 'organization_id')

    if organization_id:
        if get_organization_admins(organization_id):
            roles = [role for role in roles if role['value'] != 'editor']
        return roles
    else:
        return None


def _membeship_request_list_dictize(obj_list, context):
    """Helper to convert member requests list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = {}
        organization = model.Session.query(model.Group).get(obj.group_id)
        # Fetch the newest member_request associated to this membership (sort
        # by last modified field)
        member_request = model.Session.query(MemberRequest).filter(
            MemberRequest.membership_id == obj.id).order_by('request_date desc').limit(1).first()
        # Filter out those with cancel state as there is no need to show them to the end user
        # Show however those with 'rejected' state as user may want to know about them
        # HUOM! If a user creates itself a organization has already a
        # membership but doesnt have a member_request
        member_dict['organization_name'] = organization.name
        member_dict['organization_id'] = obj.group_id
        member_dict['role'] = 'admin'
        member_dict['state'] = 'active'
        # We use the member_request state since there is also rejected and
        # cancel
        if member_request is not None and member_request.status is not 'cancel':
            member_dict['state'] = member_request.status
            member_dict['role'] = member_request.role
            member_dict['request_date'] = member_request.request_date.strftime(
                "%d - %b - %Y")
            if member_request.handling_date:
                member_dict['handling_date'] = member_request.handling_date.strftime(
                    "%d - %b - %Y")
                member_dict['handled_by'] = member_request.handled_by
        if member_request is None or member_request.status is not 'cancel':
            result_list.append(member_dict)
    return result_list


def _member_list_dictize(obj_list, context, sort_key=lambda x: x['group_id'], reverse=False):
    """ Helper to convert member list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = model_dictize.member_dictize(obj, context)
        user = model.Session.query(model.User).get(obj.table_id)

        member_dict['group_name'] = obj.group.name
        member_dict['role'] = obj.capacity
        # Member request must always exist since state is pending. Fetch just
        # the latest
        member_request = model.Session.query(MemberRequest).filter(MemberRequest.membership_id == obj.id)\
            .filter(MemberRequest.status == 'pending').order_by('request_date desc').limit(1).first()
        # This should never happen but..
        my_date = ""
        if member_request is not None:
            my_date = member_request.request_date.strftime("%d - %b - %Y")

        member_dict['request_date'] = my_date
        member_dict['mid'] = obj.id

        member_dict['user_name'] = user.name
        result_list.append(member_dict)
    return sorted(result_list, key=sort_key, reverse=reverse)
