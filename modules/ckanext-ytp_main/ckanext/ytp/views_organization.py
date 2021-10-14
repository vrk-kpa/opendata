# encoding: utf-8

import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.model as model
from ckan.common import g, request, _, c, config
from ckan.views.group import BulkProcessView, CreateGroupView,\
                            EditGroupView, DeleteGroupView, MembersGroupView, \
                            index, about, activity, set_org, _action, \
                            _db_to_form_schema, _read, _get_group_template, \
                            member_delete, history, followers, follow, unfollow, admins, \
                            _check_access

from flask import Blueprint

log = logging.getLogger(__name__)

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action

def read(group_type, is_organization, id=None, limit=20):
    extra_vars = {}
    set_org(is_organization)
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'schema': _db_to_form_schema(group_type=group_type),
        u'for_view': True
    }
    data_dict = {u'id': id, u'type': group_type}

    # unicode format (decoded from utf8)
    q = request.params.get(u'q', u'')

    extra_vars["q"] = q

    try:
        # Do not query for the group datasets when dictizing, as they will
        # be ignored and get requested on the controller anyway
        data_dict['include_datasets'] = False

        # Do not query group members as they aren't used in the view
        data_dict['include_users'] = False

        group_dict = _action(u'group_show')(context, data_dict)
        group = context['group']
    except NotFound:
        base.abort(404, _(u'Group not found'))
    except NotAuthorized:
        group = model.Session.query(model.Group).filter(model.Group.name == id).first()
        if group is None or group.state != 'active':
            return base.render('group/organization_not_found.html', group_type=group_type)

    # if the user specified a group id, redirect to the group name
    if data_dict['id'] == group_dict['id'] and \
            data_dict['id'] != group_dict['name']:

        url_with_name = h.url_for(u'{}.read'.format(group_type),
                                  id=group_dict['name'])

        return h.redirect_to(
            h.add_url_param(alternative_url=url_with_name))

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.q = q
    g.group_dict = group_dict
    g.group = group

    extra_vars = _read(id, limit, group_type)

    extra_vars["group_type"] = group_type
    extra_vars["group_dict"] = group_dict

    return base.render(
        _get_group_template(u'read_template', g.group_dict['type']),
        extra_vars)

def members(id, group_type, is_organization):
    extra_vars = {}
    set_org(is_organization)
    context = {u'model': model, u'session': model.Session, u'user': g.user}

    try:
        data_dict = {u'id': id}
        check_access(u'group_edit_permissions', context, data_dict)
        members = get_action(u'member_list')(context, {
            u'id': id,
            u'object_type': u'user'
        })
        data_dict['include_datasets'] = False
        data_dict['include_users'] = True
        group_dict = _action(u'group_show')(context, data_dict)
        context['keep_email'] = True
        context['auth_user_obj'] = c.userobj
    except NotFound:
        base.abort(404, _(u'Group not found'))
    except NotAuthorized:
        base.abort(403,
                   _(u'User %r not authorized to edit members of %s') %
                   (g.user, id))

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.members = members
    g.group_dict = group_dict

    extra_vars = {
        u"members": members,
        u"group_dict": group_dict,
        u"group_type": group_type
    }
    return base.render(u'group/members.html', extra_vars)

def index(group_type, is_organization):
    extra_vars = {}
    set_org(is_organization)
    page = h.get_page_number(request.params) or 1
    items_per_page = int(config.get(u'ckan.datasets_per_page', 20))

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }

    try:
        _check_access(u'site_read', context)
        _check_access(u'group_list', context)
    except NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    q = request.params.get(u'q', u'')
    sort_by = request.params.get(u'sort')

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.q = q
    g.sort_by_selected = sort_by

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if g.userobj:
        context['user_id'] = g.userobj.id
        context['user_is_admin'] = g.userobj.sysadmin

    try:
        data_dict_global_results = {
            u'all_fields': False,
            u'q': q,
            u'sort': sort_by,
            u'type': group_type or u'group',
        }
        global_results = _action(u'group_list')(context,
                                                data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get(u'message'):
            msg = e.error_dict['message']
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = h.Page([], 0)
        extra_vars["group_type"] = group_type
        return base.render(
            _get_group_template(u'index_template', group_type), extra_vars)

    c.with_datasets = with_datasets = request.params.get('with_datasets', '').lower() in ('true', '1', 'yes')
    tree_list_params = {
                    'q': q, 'sort_by': sort_by, 'with_datasets': with_datasets,
                    'page': page, 'items_per_page': items_per_page}
    page_results = _action(u'organization_tree_list')(context, tree_list_params)

    extra_vars["page"] = h.Page(
        collection=global_results,
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
        _get_group_template(u'index_template', group_type), extra_vars)


organization = Blueprint(u'ytp_organization', __name__,
                         url_prefix=u'/organization',
                         url_defaults={u'group_type': u'organization',
                                       u'is_organization': True})


def register_group_plugin_rules(blueprint):
    actions = [
        u'member_delete', u'history', u'followers', u'follow',
        u'unfollow', u'admins', u'activity'
    ]
    blueprint.add_url_rule(u'/', view_func=index, strict_slashes=False)
    blueprint.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateGroupView.as_view(str(u'new')))
    blueprint.add_url_rule(u'/<id>', methods=[u'GET'], view_func=read)
    blueprint.add_url_rule(
        u'/edit/<id>', view_func=EditGroupView.as_view(str(u'edit')))
    blueprint.add_url_rule(
        u'/activity/<id>/<int:offset>', methods=[u'GET'], view_func=activity)
    blueprint.add_url_rule(u'/about/<id>', methods=[u'GET'], view_func=about)
    blueprint.add_url_rule(
        u'/members/<id>', methods=[u'GET', u'POST'], view_func=members)
    blueprint.add_url_rule(
        u'/member_new/<id>',
        view_func=MembersGroupView.as_view(str(u'member_new')))
    blueprint.add_url_rule(
        u'/bulk_process/<id>',
        view_func=BulkProcessView.as_view(str(u'bulk_process')))
    blueprint.add_url_rule(
        u'/delete/<id>',
        methods=[u'GET', u'POST'],
        view_func=DeleteGroupView.as_view(str(u'delete')))
    for action in actions:
        blueprint.add_url_rule(
            u'/{0}/<id>'.format(action),
            methods=[u'GET', u'POST'],
            view_func=globals()[action])


register_group_plugin_rules(organization)

def get_blueprints():
    return [organization]