# encoding: utf-8

import logging
from typing import Any, Optional, Union, cast

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckan.lib.helpers import Page
from ckan.plugins import toolkit
from ckan.types import Context
from ckan.views.group import (
    BulkProcessView,
    CreateGroupView,
    DeleteGroupView,
    EditGroupView,
    MembersGroupView,
    _db_to_form_schema,
    _get_group_template,
    _read,
    _setup_template_variables,
    about,
    admins,
    follow,
    followers,
    member_delete,
    unfollow,
)
from flask import Blueprint
from flask.wrappers import Response

from ckanext.organizationapproval.logic import send_new_organization_email_to_admin

log = logging.getLogger(__name__)

NotFound = toolkit.ObjectNotFound
NotAuthorized = toolkit.NotAuthorized
ValidationError = toolkit.ValidationError
check_access = toolkit.check_access
get_action = toolkit.get_action
abort = toolkit.abort
render = toolkit.render
g = toolkit.g
request = toolkit.request
_ = toolkit._
config = toolkit.config
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params



class CreateOrganizationView(CreateGroupView):
    '''Create organization view '''

    def _prepare(self, is_organization: bool = True, data: Optional[dict[str, Any]] = None) -> Context:
        group_type = 'organization'
        if data:
            data['type'] = group_type

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': toolkit.current_user.name,
            'save': 'save' in request.args,
            'parent': request.args.get('parent', None),
            'group_type': group_type
        })

        try:
            toolkit.check_access('organization_create', context)
        except NotAuthorized:
            base.abort(403, _('Unauthorized to create a group'))

        return context

    def post(self, group_type: str, is_organization: bool) -> Union[Response, str]:
        if not is_organization:
            return base.abort(400, 'Not an organization')

        context = self._prepare()
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
        except dict_fns.DataError:
            return base.abort(400, _('Integrity Error'))
        user = toolkit.current_user.name
        data_dict['type'] = group_type or 'group'
        context['message'] = data_dict.get('log_message', '')
        data_dict['users'] = [{'name': user, 'capacity': 'admin'}]
        data_dict['approval_status'] = 'pending'
        try:
            group = get_action('organization_create')(context, data_dict)
            send_new_organization_email_to_admin()
        except (NotFound, NotAuthorized):
            return base.abort(404, _('Group not found'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(group_type, True,
                            data_dict, errors, error_summary)

        return h.redirect_to(
            group['type'] + '.read', id=group['name'])


class EditOrganizationView(EditGroupView):
    '''Edit organization view '''

    def get(self,
            id: str,
            group_type: str,
            is_organization: bool,
            data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None) -> str:

        if not is_organization:
            return base.abort(400, 'Not an organization')

        context = self._prepare(is_organization, id=id)
        data_dict: dict[str, Any] = {'id': id, 'include_datasets': False}
        try:
            action_name = (
                'organization_show' if is_organization else 'group_show'
            )
            group_dict = get_action(action_name)(context, data_dict)
        except (NotFound, NotAuthorized):
            return base.abort(404, _('Group not found'))
        data = data or group_dict
        assert data is not None

        for extra in data.get('extras', []):
            if extra.get('key') == 'features':
                # Convert old features field to match with new radiobuttons
                data = {**data, **{
                    'public_administration_organization': 'public_administration_organization' in extra.get('value'),
                    'edit_only_owned_datasets': 'personal_datasets' in extra.get('value'),
                }}

        errors = errors or {}
        extra_vars: dict[str, Any] = {
            'data': data,
            "group_dict": group_dict,
            'errors': errors,
            'error_summary': error_summary,
            'action': 'edit',
            'group_type': group_type
        }

        _setup_template_variables(context, data, group_type=group_type)
        form = base.render(
            _get_group_template('group_form', group_type), extra_vars)

        # TODO: Remove
        # ckan 2.9: Adding variables that were removed from c object for
        # compatibility with templates in existing extensions
        g.grouptitle = group_dict.get('title')
        g.groupname = group_dict.get('name')
        g.data = data
        g.group_dict = group_dict

        extra_vars["form"] = form
        return base.render(
            _get_group_template(u'edit_template', group_type), extra_vars)


def read(group_type: str,
         is_organization: bool,
         id: Optional[str] = None,
         limit: Optional[int] = None) -> Union[str, Response]:
    if not is_organization:
        return base.abort(400, 'Not an organization')

    extra_vars = {}
    context: Context = {
        'user': toolkit.current_user.name,
        'schema': _db_to_form_schema(group_type=group_type),
        'for_view': True
    }
    data_dict: dict[str, Any] = {'id': id, 'type': group_type}

    # unicode format (decoded from utf8)
    q = request.args.get('q', '')

    extra_vars["q"] = q

    limit = limit or config.get('ckan.datasets_per_page')

    try:
        # Do not query for the group datasets when dictizing, as they will
        # be ignored and get requested on the controller anyway
        data_dict['include_datasets'] = False

        # Do not query group members as they aren't used in the view
        data_dict['include_users'] = False

        group_dict = get_action('organization_show')(context, data_dict)
    except (NotFound, NotAuthorized):
        return base.abort(404, _('Group not found'))

    # if the user specified a group id, redirect to the group name
    if data_dict['id'] == group_dict['id'] and \
            data_dict['id'] != group_dict['name']:

        url_with_name = h.url_for('{}.read'.format(group_type),
                                  id=group_dict['name'])

        return h.redirect_to(
            h.add_url_param(alternative_url=url_with_name))

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.q = q
    g.group_dict = group_dict

    extra_vars = _read(id, limit, group_type)
    try:
        am_following = logic.get_action('am_following_group')(
            {'user': toolkit.current_user.name}, {'id': id}
        )
    except NotAuthorized:
        # AnonymousUser
        am_following = False

    extra_vars["group_type"] = group_type
    extra_vars["group_dict"] = group_dict
    extra_vars["am_following"] = am_following

    return base.render(
        _get_group_template(u'read_template', g.group_dict['type']),
        extra_vars)


def members(id: str, group_type: str, is_organization: bool) -> str:
    if not is_organization:
        return base.abort(400, 'Not an organization')

    context: Context = {'user': toolkit.current_user.name}

    try:
        data_dict: dict[str, Any] = {'id': id}
        check_access('group_edit_permissions', context, data_dict)
        members = get_action('member_list')(context, {
            'id': id,
            'object_type': 'user'
        })
        data_dict['include_datasets'] = False
        data_dict['include_users'] = True
        context['keep_email'] = True
        context['auth_user_obj'] = g.userobj
        group_dict = get_action('organization_show')(context, data_dict)
    except NotFound:
        return base.abort(404, _('Group not found'))
    except NotAuthorized:
        return base.abort(403,
                   _('User %r not authorized to edit members of %s') %
                   (toolkit.current_user.name, id))

    extra_vars: dict[str, Any] = {
        "members": members,
        "group_dict": group_dict,
        "group_type": group_type,
    }

    return base.render('organization/members.html', extra_vars)


# kwargs needed because of blueprint default parameters
def user_list(**kwargs):
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'userobj': g.userobj}
    extra_vars = {}

    try:
        check_access('user_list', context, {})

        q = model.Session.query(model.Group, model.Member, model.User). \
            filter(model.Member.group_id == model.Group.id). \
            filter(model.Member.table_id == model.User.id). \
            filter(model.Member.table_name == 'user'). \
            filter(model.User.name != 'harvest'). \
            filter(model.User.name != 'default'). \
            filter(model.User.state == 'active'). \
            filter(model.Group.is_organization == 'true')

        users = {}

        for group, member, user in q.all():

            user_obj = users.get(user.name, {})
            if user_obj == {}:
                user_obj = {
                    'user_id': user.id,
                    'username': user.name,
                    'organizations': [group.display_name],
                    'roles': [member.capacity],
                    'email': user.email
                }
            else:
                user_obj['organizations'].append(group.display_name)
                if member.capacity not in user_obj['roles']:
                    user_obj['roles'].append(member.capacity)

            users[user.name] = user_obj

        g.users = users
        extra_vars['users'] = users

        return base.render('organization/user_list.html', extra_vars)

    except NotAuthorized:
        abort(403, _('Only system administrators are allowed to view user list.'))


# kwargs needed because of blueprint default parameters
def admin_list(**kwargs):
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'userobj': g.userobj}
    extra_vars = {}

    try:
        check_access('user_list', context, {})

        q = model.Session.query(model.Group, model.Member, model.User). \
            filter(model.Member.group_id == model.Group.id). \
            filter(model.Member.table_id == model.User.id). \
            filter(model.Member.table_name == 'user'). \
            filter(model.Member.capacity == 'admin'). \
            filter(model.User.name != 'harvest'). \
            filter(model.User.name != 'default'). \
            filter(model.User.state == 'active'). \
            filter(model.Group.is_organization == 'true')

        users = {}

        for group, member, user in q.all():

            user_obj = users.get(user.name, {})
            if user_obj == {}:
                user_obj = {
                    'user_id': user.id,
                    'username': user.name,
                    'organizations': [group.display_name],
                    'roles': [member.capacity],
                    'email': user.email
                }
            else:
                user_obj['organizations'].append(group.display_name)
                if member.capacity not in user_obj['roles']:
                    user_obj['roles'].append(member.capacity)

            users[user.name] = user_obj

        g.users = users
        extra_vars['users'] = users

        return base.render('organization/admin_list.html', extra_vars)

    except NotAuthorized:
        abort(403, _('Only system administrators are allowed to view user list.'))


def index(group_type: str, is_organization: bool) -> str:
    if not is_organization:
        return base.abort(400, 'Not an organization')

    extra_vars: dict[str, Any] = {}
    page = h.get_page_number(request.args) or 1
    items_per_page = config.get('ckan.datasets_per_page')

    context: Context = {
        u'user': toolkit.current_user.name,
        u'for_view': True,
        u'with_private': False,
    }

    try:
        action_name = 'organization_list' if is_organization else 'group_list'
        check_access(action_name, context)
    except NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    q = request.args.get(u'q', u'')
    sort_by = request.args.get(u'sort')

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.q = q
    g.sort_by_selected = sort_by

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if toolkit.current_user.is_authenticated:
        context['user_id'] = toolkit.current_user.id
        context['user_is_admin'] = toolkit.current_user.sysadmin  # type: ignore

    # Check if to display all organizations or only those that have datasets
    only_with_datasets_param = request.args.get('only_with_datasets', "False").lower() in ['true', True, 1, ]
    extra_vars['only_with_datasets'] = only_with_datasets_param
    with_datasets = only_with_datasets_param

    tree_list_params = {
                    'q': q, 'sort_by': sort_by, 'with_datasets': with_datasets,
                    'page': page, 'items_per_page': items_per_page}
    page_results = toolkit.get_action('organization_tree_list')(context, tree_list_params)

    extra_vars["page"] = Page(
        collection=page_results['global_results'],
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page, )

    extra_vars["page"].items = page_results['page_results']
    extra_vars["group_type"] = group_type

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.page = extra_vars["page"]
    return base.render(
        _get_group_template('index_template', group_type), extra_vars)


def suborganizations(id, group_type, is_organization):
    try:

        context = {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'for_view': True
        }

        group_dict = get_action('organization_show')(context, {'id': id, 'include_datasets': False})

        extra_vars = {
            'group_dict': group_dict,
            'group_type': group_type
        }
        return render("organization/suborganizations.html", extra_vars=extra_vars)
    except (NotFound, NotAuthorized):
        abort(404, _('Organization not found'))

    


organization = Blueprint('ytp_organization', __name__,
                         url_defaults={'group_type': 'organization',
                                       'is_organization': True})

organization.add_url_rule('/organization', view_func=index, strict_slashes=False)
organization.add_url_rule(
    '/organization/new',
    methods=['GET', 'POST'],
    view_func=CreateOrganizationView.as_view(str('new')))
organization.add_url_rule('/organization/<id>', methods=['GET'], view_func=read)
organization.add_url_rule(
    '/organization/edit/<id>', view_func=EditOrganizationView.as_view(str('edit')))
organization.add_url_rule('/organization/about/<id>', methods=['GET'], view_func=about)
organization.add_url_rule(
    '/organization/members/<id>', methods=['GET', 'POST'], view_func=members)
organization.add_url_rule(
    '/organization/member_new/<id>',
    view_func=MembersGroupView.as_view(str('member_new')))
organization.add_url_rule(
    '/organization/bulk_process/<id>',
    view_func=BulkProcessView.as_view(str('bulk_process')))
organization.add_url_rule(
    '/organization/delete/<id>',
    methods=['GET', 'POST'],
    view_func=DeleteGroupView.as_view(str('delete')))
organization.add_url_rule(
    '/organization/member_delete/<id>',
    methods=['GET', 'POST'],
    view_func=member_delete)
organization.add_url_rule(
    '/organization/followers/<id>',
    methods=['GET', 'POST'],
    view_func=followers)
organization.add_url_rule(
    '/organization/follow/<id>',
    methods=['GET', 'POST'],
    view_func=follow)
organization.add_url_rule(
    '/organization/unfollow/<id>',
    methods=['GET', 'POST'],
    view_func=unfollow)
organization.add_url_rule(
    '/organization/admins/<id>',
    methods=['GET', 'POST'],
    view_func=admins)
organization.add_url_rule(
    '/admin_list', methods=['GET'], view_func=admin_list)
organization.add_url_rule(
    '/user_list', methods=['GET'], view_func=user_list)
organization.add_url_rule('/organization/suborganizations/<id>', view_func=suborganizations)

def get_blueprints():
    return [organization]
