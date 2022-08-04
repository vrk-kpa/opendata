from flask import Blueprint
from ckan.plugins import toolkit
from ckan import logic, model, authz


not_auth_message = toolkit._('Unauthorized')
request_not_found_message = toolkit._('Request not found')


member_request = Blueprint('member_request', __name__, url_prefix='/member-request')


def get_blueprint():
    return [member_request]


@member_request.route('/new', methods=['GET', 'POST'])
def new(errors=None, error_summary=None):
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author'),
               'save': 'save' in toolkit.request.args}
    try:
        toolkit.check_access('member_request_create', context)
    except toolkit.NotAuthorized:
        toolkit.abort(401, not_auth_message)

    organizations = toolkit.get_action('organization_list_without_memberships')(context, {})

    if toolkit.request.method == 'POST' and not errors:
        success, results = _save_new(context)
        if success:
            member_id = results
            return toolkit.redirect_to('organization.index', id="newrequest", membership_id=member_id)
        else:
            errors, error_summary = results

    # FIXME: Don't send as request parameter selected organization. kinda
    # weird
    selected_organization = toolkit.request.args.get(
        'selected_organization', None)
    roles = _get_available_roles(context, selected_organization)
    user_role = 'admin'

    extra_vars = {'selected_organization': selected_organization, 'organizations': organizations,
                  'errors': errors or {}, 'error_summary': error_summary or {},
                  'roles': roles, 'user_role': user_role}
    extra_vars['form'] = toolkit.render("request/new_request_form.html", extra_vars=extra_vars)
    return toolkit.render("request/new.html", extra_vars=extra_vars)


def _save_new(context):
    errors = None
    error_summary = None
    try:
        data_dict = {
                'user': toolkit.g.user,
                'role': toolkit.get_or_bust(toolkit.request.form, 'role'),
                'group': toolkit.get_or_bust(toolkit.request.form, 'organization')}

        # TODO: Do we need info message at the UI level when e-mail could
        # not be sent?
        member = toolkit.get_action(
            'member_request_create')(context, data_dict)
        return (True, member['id'])
    except logic.NotFound:
        toolkit.abort(404, toolkit._('Item not found'))
    except logic.NotAuthorized:
        toolkit.abort(405, not_auth_message)
    except logic.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
    return (False, (errors, error_summary))


@member_request.route('/mylist')
def mylist():
    """" Lists own members requests (possibility to cancel and view current status)"""
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    id = toolkit.request.args.get('id', None)
    if not authz.is_sysadmin(toolkit.c.user):
        try:
            my_requests = toolkit.get_action(
                'member_requests_mylist')(context, {})
            message = None
            if id:
                message = toolkit._("Member request processed successfully")
            extra_vars = {'my_requests': my_requests, 'message': message}
            return toolkit.render('request/mylist.html', extra_vars=extra_vars)
        except logic.NotAuthorized:
            toolkit.abort(401, not_auth_message)
    else:
        return toolkit.render('request/mylist.html', extra_vars={
            'my_requests': [],
            'message': toolkit._("As a sysadmin, you already have access to all organizations")})


@member_request.route('/list')
def member_requests_list():
    """ Lists member requests to be approved by admins"""
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    id = toolkit.request.args.get('id', None)
    try:
        member_requests = toolkit.get_action(
            'member_requests_list')(context, {})
        message = None
        if id:
            message = toolkit._("Member request processed successfully")
        extra_vars = {
            'member_requests': member_requests, 'message': message}
        return toolkit.render('request/list.html', extra_vars=extra_vars)
    except logic.NotAuthorized:
        toolkit.abort(401, not_auth_message)


@member_request.route('/reject/<mrequest_id>', methods=['GET', 'POST'])
def reject(mrequest_id):
    """ Controller to reject member request (only admins or group editors can do that """
    return _processbyadmin(mrequest_id, False)


@member_request.route('/approve/<mrequest_id>', methods=['GET', 'POST'])
def approve(mrequest_id):
    """ Controller to approve member request (only admins or group editors can do that) """
    return _processbyadmin(mrequest_id, True)


@member_request.route('/cancel', methods=['GET', 'POST'])
def cancel():
    """ Logged in user can cancel pending requests not approved yet by admins/editors"""
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    organization_id = toolkit.request.args.get('organization_id', None)
    try:
        toolkit.get_action('member_request_cancel')(
            context, {"organization_id": organization_id})
        id = 'cancel'
        return toolkit.redirect_to('member_request.mylist', id=id)
    except logic.NotAuthorized:
        toolkit.abort(401, not_auth_message)
    except logic.NotFound:
        toolkit.abort(404, request_not_found_message)


@member_request.route('/membership-cancel/<organization_id>', methods=['GET', 'POST'])
def membership_cancel(organization_id):
    """ Logged in user can cancel already approved/existing memberships """
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    try:
        toolkit.get_action('member_request_membership_cancel')(
            context, {"organization_id": organization_id})
        id = 'cancel'
        return toolkit.redirect_to('member_request.mylist', id=id)
    except logic.NotAuthorized:
        toolkit.abort(401, not_auth_message)
    except logic.NotFound:
        toolkit.abort(404, request_not_found_message)


@member_request.route('/<mrequest_id>')
def show(mrequest_id):
    """" Shows a single member request.
    To be used by admins in case they want to modify granted role or accept via e-mail """
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    try:
        membershipdto = toolkit.get_action('member_request_show')(
            context, {'mrequest_id': mrequest_id})
        member_user = model.Session.query(
            model.User).get(membershipdto['user_id'])
        context = {'user': member_user.name}
        roles = _get_available_roles(
            context, membershipdto['organization_name'])
        extra_vars = {"membership": membershipdto,
                      "member_user": member_user, "roles": roles}
        return toolkit.render('request/show.html', extra_vars=extra_vars)
    except logic.NotFound:
        toolkit.abort(404, request_not_found_message)
    except logic.NotAuthorized:
        toolkit.abort(401, not_auth_message)


def _get_available_roles(context, organization_id):
    data_dict = {'organization_id': organization_id}
    return toolkit.get_action('get_available_roles')(context, data_dict)


def _processbyadmin(mrequest_id, approve):
    context = {'user': toolkit.g.get('user') or toolkit.g.get('author')}
    role = toolkit.request.args.get('role', None)
    data_dict = {"mrequest_id": mrequest_id, 'role': role}
    try:
        if approve:
            toolkit.get_action('member_request_approve')(
                context, data_dict)
            id = 'approved'
        else:
            toolkit.get_action('member_request_reject')(context, data_dict)
            id = 'rejected'
        return toolkit.redirect_to('member_request.member_requests_list', id=id)
    except logic.NotAuthorized:
        toolkit.abort(401, not_auth_message)
    except logic.NotFound:
        toolkit.abort(404, request_not_found_message)
    except logic.ValidationError as e:
        toolkit.abort(400, str(e))
