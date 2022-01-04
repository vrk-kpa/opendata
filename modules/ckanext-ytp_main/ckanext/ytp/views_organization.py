# encoding: utf-8

import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.common import g, request, _, c, config
from ckan.views.group import BulkProcessView, CreateGroupView,\
                            EditGroupView, DeleteGroupView, MembersGroupView, \
                            about, activity, set_org, _action, _check_access, \
                            _db_to_form_schema, _read, _get_group_template, \
                            member_delete, history, followers, follow, unfollow, admins
from ckanext.organizationapproval.logic import send_new_organization_email_to_admin

from flask import Blueprint

log = logging.getLogger(__name__)

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
abort = base.abort
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params


class CreateOrganizationView(CreateGroupView):
    '''Create organization view '''

    def _prepare(self, data=None):
        group_type = 'organization'
        if data:
            data['type'] = group_type

        context = {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'save': 'save' in request.params,
            'parent': request.params.get('parent', None),
            'group_type': group_type
        }

        try:
            _check_access('group_create', context)
        except NotAuthorized:
            base.abort(403, _('Unauthorized to create a group'))

        return context

    def post(self, group_type, is_organization):
        set_org(is_organization)
        context = self._prepare()
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
            data_dict['type'] = group_type or 'group'
            context['message'] = data_dict.get('log_message', '')
            data_dict['users'] = [{'name': g.user, 'capacity': 'admin'}]
            data_dict['approval_status'] = 'pending'

            group = _action('group_create')(context, data_dict)
            send_new_organization_email_to_admin()
        except (NotFound, NotAuthorized):
            base.abort(404, _('Group not found'))
        except dict_fns.DataError:
            base.abort(400, _('Integrity Error'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(group_type, is_organization,
                            data_dict, errors, error_summary)

        return h.redirect_to(group['type'] + '.read', id=group['name'])


def read(group_type, is_organization, id=None, limit=20):
    extra_vars = {}
    set_org(is_organization)
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'schema': _db_to_form_schema(group_type=group_type),
        'for_view': True
    }
    data_dict = {'id': id, 'type': group_type}

    # unicode format (decoded from utf8)
    q = request.params.get('q', '')

    extra_vars["q"] = q

    try:
        # Do not query for the group datasets when dictizing, as they will
        # be ignored and get requested on the controller anyway
        data_dict['include_datasets'] = False

        # Do not query group members as they aren't used in the view
        data_dict['include_users'] = False

        group_dict = _action('group_show')(context, data_dict)
        group = context['group']
    except NotFound:
        base.abort(404, _('Group not found'))
    except NotAuthorized:
        group = model.Session.query(model.Group).filter(model.Group.name == id).first()
        if group is None or group.state != 'active':
            return base.render('group/organization_not_found.html', group_type=group_type)

    # if the user specified a group id, redirect to the group name
    if data_dict['id'] == group_dict['id'] and \
            data_dict['id'] != group_dict['name']:

        url_with_name = h.url_for('{}.read'.format(group_type),
                                  id=group_dict['name'])

        return h.redirect_to(
            h.add_url_param(alternative_url=url_with_name))

    # Needed by ckan/views/group::_read
    g.q = q
    g.group_dict = group_dict
    g.group = group

    extra_vars = _read(id, limit, group_type)

    extra_vars["group_type"] = group_type
    extra_vars["group_dict"] = group_dict

    return base.render(
        _get_group_template('read_template', g.group_dict['type']),
        extra_vars)


def members(id, group_type, is_organization):
    extra_vars = {}
    set_org(is_organization)
    context = {'model': model, 'session': model.Session, 'user': g.user}

    try:
        data_dict = {'id': id}
        check_access('group_edit_permissions', context, data_dict)
        members = get_action('member_list')(context, {
            'id': id,
            'object_type': 'user'
        })
        data_dict['include_datasets'] = False
        data_dict['include_users'] = True
        group_dict = _action('group_show')(context, data_dict)
        context['keep_email'] = True
        context['auth_user_obj'] = c.userobj
    except NotFound:
        base.abort(404, _('Group not found'))
    except NotAuthorized:
        base.abort(403,
                   _('User %r not authorized to edit members of %s') %
                   (g.user, id))

    extra_vars = {
        "members": members,
        "group_dict": group_dict,
        "group_type": group_type
    }
    return base.render('group/members.html', extra_vars)


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

        c.users = users
        extra_vars['users'] = users

        return base.render('organization/user_list.html', extra_vars)

    except NotAuthorized:
        abort(403, _('Only system administrators are allowed to view user list.'))


# kwargs needed because of blueprint default parameters
def admin_list(**kwargs):
    context = {'model': model, 'session': model.Session,
               'user': c.user, 'userobj': c.userobj}
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

        c.users = users
        extra_vars['users'] = users

        return base.render('organization/admin_list.html', extra_vars)

    except NotAuthorized:
        abort(403, _('Only system administrators are allowed to view user list.'))


def index(group_type, is_organization):
    extra_vars = {}
    set_org(is_organization)
    page = h.get_page_number(request.params) or 1
    items_per_page = int(config.get('ckan.datasets_per_page', 20))

    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'for_view': True,
        'with_private': False
    }

    try:
        _check_access('site_read', context)
        _check_access('group_list', context)
    except NotAuthorized:
        base.abort(403, _('Not authorized to see this page'))

    q = request.params.get('q', '')
    sort_by = request.params.get('sort')

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if g.userobj:
        context['user_id'] = g.userobj.id
        context['user_is_admin'] = g.userobj.sysadmin

    try:
        data_dict_global_results = {
            'all_fields': False,
            'q': q,
            'sort': sort_by,
            'type': group_type or 'group',
        }
        global_results = _action('group_list')(context,
                                               data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get('message'):
            msg = e.error_dict['message']
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = h.Page([], 0)
        extra_vars["group_type"] = group_type
        return base.render(
            _get_group_template('index_template', group_type), extra_vars)

    extra_vars['with_datasets'] = with_datasets = request.params.get('with_datasets', '').lower() in ('true', '1', 'yes')
    tree_list_params = {
                    'q': q, 'sort_by': sort_by, 'with_datasets': with_datasets,
                    'page': page, 'items_per_page': items_per_page}
    page_results = _action('organization_tree_list')(context, tree_list_params)

    extra_vars["page"] = h.Page(
        collection=global_results,
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page, )

    extra_vars["page"].items = page_results['page_results']
    extra_vars["group_type"] = group_type

    return base.render(
        _get_group_template('index_template', group_type), extra_vars)


def embed(id, group_type, is_organization, limit=5):
    """
        Fetch given organization's packages and show them in an embeddable list view.
        See Nginx config for X-Frame-Options SAMEORIGIN header modifications.
    """

    def make_pager_url(q=None, page=None):
        ctrlr = 'ckanext.ytp.controller:YtpOrganizationController'
        url = h.url_for(controller=ctrlr, action='embed', id=id)
        return url + '?page=' + str(page)

    extra_vars = {}

    try:
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author
        }
        check_access('group_show', context, {'id': id})
    except NotFound:
        abort(404, _('Group not found'))
    except NotAuthorized:
        g = model.Session.query(model.Group).filter(model.Group.name == id).first()
        if g is None or g.state != 'active':
            return base.render('group/organization_not_found.html')

    page = h.get_page_number(request.params) or 1

    group_dict = {'id': id}
    group_dict['include_datasets'] = False
    c.group_dict = _action('group_show')(context, group_dict)
    c.group = context['group']

    q = c.q = request.params.get('q', '')
    q += ' owner_org:"%s"' % c.group_dict.get('id')

    data_dict = {
        'q': q,
        'rows': limit,
        'start': (page - 1) * limit,
        'extras': {}
    }

    query = get_action('package_search')(context, data_dict)

    c.page = h.Page(
        collection=query['results'],
        page=page,
        url=make_pager_url,
        item_count=query['count'],
        items_per_page=limit
    )

    c.page.items = query['results']

    return base.render("organization/embed.html", extra_vars)


organization = Blueprint('ytp_organization', __name__,
                         url_defaults={'group_type': 'organization',
                                       'is_organization': True})

organization.add_url_rule('/organization', view_func=index, strict_slashes=False)
organization.add_url_rule(
    '/organization/new',
    methods=['GET', 'POST'],
    view_func=CreateOrganizationView.as_view(str('new')))
organization.add_url_rule('/organization/<id>', methods=['GET'], view_func=read)
organization.add_url_rule('/organization/<id>/embed', methods=['GET'], view_func=embed)
organization.add_url_rule(
    '/organization/edit/<id>', view_func=EditGroupView.as_view(str('edit')))
organization.add_url_rule(
    '/organization/activity/<id>/<int:offset>', methods=['GET'], view_func=activity)
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
    '/organization/history/<id>',
    methods=['GET', 'POST'],
    view_func=history)
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
    '/organization/activity/<id>',
    methods=['GET', 'POST'],
    view_func=activity)
organization.add_url_rule(
    '/admin_list', methods=['GET'], view_func=admin_list)
organization.add_url_rule(
    '/user_list', methods=['GET'], view_func=user_list)


def get_blueprints():
    return [organization]
