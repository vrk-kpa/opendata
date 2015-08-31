from ckan import model
from ckan.logic import NotFound
from ckan.lib.dictization import model_dictize

import logic
import logging
import ckan.new_authz as authz

log = logging.getLogger(__name__)

def member_requests_mylist(context, data_dict):
    ''' Users wil see a list of her member requests
    '''
    logic.check_access('member_requests_mylist', context, data_dict)

    user = context['user']
    user_object = model.User.get(user)
    is_sysadmin = authz.is_sysadmin(user)

    query = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.table_id == user_object.id)

    members = query.all()

    return _member_list_dictize(members, context)

def member_requests_list(context, data_dict):
    ''' Organization admins/editors will see a list of member requests to be approved.
    :param group: name of the group (optional)
    :type group: string
    '''
    logic.check_access('member_requests_list', context, data_dict)

    user = context['user']
    user_object = model.User.get(user)
    is_sysadmin = authz.is_sysadmin(user)

    query = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.state == 'pending')

    if not is_sysadmin:
        admin_in_groups = model.Session.query(model.Member).filter(model.Member.state == "active").filter(model.Member.table_name == "user") \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user_object.id)

        if admin_in_groups.count() <= 0:
            return []

        query = query.filter(model.Member.group_id.in_(admin_in_groups.values(model.Member.group_id)))

    group = data_dict.get('group', None)
    if group:
        group_object = model.Group.get(group)
        if group_object:
            query = query.filter(model.Member.group_id == group_object.id)

    members = query.all()

    return _member_list_dictize(members, context)

def member_request_show(context, data_dict):
    ''' Create new member request. User is taken from context.
    :param member: id of the member object
    :type member: string
    :param fetch_user: fetch related user data
    :type fetch_user: boolean
    '''
    logic.check_access('member_request_show', context, data_dict)

    model = context['model']
    member_id = data_dict.get("member")
    fetch_user = data_dict.get("fetch_user", False)
    member = model.Session.query(model.Member).get(member_id)

    if not member.group.is_organization:
        raise NotFound

    data = model_dictize.member_dictize(member, context)

    if fetch_user:
        member_user = model.Session.query(model.User).get(member.table_id)
        data['user'] = model_dictize.user_dictize(member_user, context)

    return data

def _member_list_dictize(obj_list, context, sort_key=lambda x: x['group_id'], reverse=False):
    """ Helper to convert member list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = model_dictize.member_dictize(obj, context)
        member_dict['group_name'] = obj.group.name
        user = model.Session.query(model.User).get(obj.table_id)
        member_dict['user_name'] = user.name
        result_list.append(member_dict)
    return sorted(result_list, key=sort_key, reverse=reverse)