from ckan import model
from ckan.logic import NotFound, ValidationError
from ckan.lib.dictization import model_dictize
from ckanext.ytp.request.model import MemberRequest
from ckanext.ytp.request.helper import get_organization_admins
from sqlalchemy import or_
import logic
import logging
import ckan.new_authz as authz


log = logging.getLogger(__name__)

def member_requests_mylist(context, data_dict):
    ''' Users wil see a list of her member requests
    '''
    logic.check_access('member_requests_mylist', context, data_dict)

    user = context.get('user',None)
    if authz.is_sysadmin(user):
        raise ValidationError({}, {_("Role"): _("As a sysadmin, you already have access to all organizations")})
        
    user_object = model.User.get(user)
    #Return current state for memberships for all organizations for the user in context. (last request date)
    #We need to use MemberRequest table since there is loss of semantics when using model.Member table as it is just DELETED there (CANCEL state is the same than REJECTED)
    membership_requests = model.Session.query(MemberRequest).join(model.Member, MemberRequest.membership_id == model.Member.id).filter(model.Member.table_id == user_object.id)  
    log.info("HELLO: %s",membership_requests)
    return _membeship_request_list_dictize(membership_requests, user_object, context)

def member_requests_list(context, data_dict):
    ''' Organization admins/editors will see a list of member requests to be approved.
    :param group: name of the group (optional)
    :type group: string
    '''
    logic.check_access('member_requests_list', context, data_dict)

    user = context.get('user',None)
    user_object = model.User.get(user)
    is_sysadmin = authz.is_sysadmin(user)

    # ALL members with pending state only
    query = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.state == 'pending')

    if not is_sysadmin:
        admin_in_groups = model.Session.query(model.Member).filter(model.Member.state == "active").filter(model.Member.table_name == "user") \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user_object.id)

        if admin_in_groups.count() <= 0:
            return []
        #members requests for this organization
        query = query.filter(model.Member.group_id.in_(admin_in_groups.values(model.Member.group_id)))

    group = data_dict.get('group', None)
    if group:
        group_object = model.Group.get(group)
        if group_object:
            query = query.filter(model.Member.group_id == group_object.id)

    members = query.all()

    return _member_list_dictize(members, context)

@logic.side_effect_free
def get_available_roles(context, data_dict=None):    
    roles = logic.get_action("member_roles_list")(context,{})

    #Remove member role from the list
    roles = [role for role in roles if role['value'] != 'member']
    
    #If organization has no associated admin, then role editor is not available
    model = context['model']
    organization_id = logic.get_or_bust(data_dict, 'organization_id')

    if organization_id:
        if get_organization_admins(organization_id):
            roles = [role for role in roles if role['value'] != 'editor']
        return roles
    else:
        return None

def _membeship_request_list_dictize(obj_list, user, context):
    """Helper to convert member requests list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = {}
        organization = model.Session.query(model.Group).get(obj.group_id)
        #There can be only active or pending so this logic is valid (one-to-one in this case)
        member_request = model.Session.query(MemberRequest).filter(MemberRequest.membership_id == obj.id).filter(MemberRequest.status == obj.state).first()
        member_dict['member_name'] = user.name
        member_dict['organization_name'] = organization.name
        member_dict['organization_id'] = obj.group_id
        member_dict['state'] = obj.state
        member_dict['role'] = member_request.role
        member_dict['request_date'] = member_request.request_date.strftime("%d - %b - %Y")
        member_dict['handling_date'] = None
        if obj.handling_date:
            member_dict['handling_date'] = member_request.handling_date.strftime("%d - %b - %Y")
        result_list.append(member_dict)
    return result_list

def _member_list_dictize(obj_list, context, sort_key=lambda x: x['group_id'], reverse=False):
    """ Helper to convert member list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = model_dictize.member_dictize(obj, context)
        member_dict['group_name'] = obj.group.name
        member_request = model.Session.query(MemberRequest).filter(MemberRequest.member_id == obj.table_id).filter(MemberRequest.organization_id == obj.group_id ).first()
        member_dict['role'] = member_request.role
        member_dict['request_date'] = member_request.request_date.strftime("%d - %b - %Y")
        member_dict['mid'] = member_request.id
        user = model.Session.query(model.User).get(obj.table_id)
        member_dict['user_name'] = user.name
        result_list.append(member_dict)
    return sorted(result_list, key=sort_key, reverse=reverse)

