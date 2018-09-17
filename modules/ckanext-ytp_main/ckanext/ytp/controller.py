import cgi
import sqlalchemy
import logging


from ckan import model
from ckan.common import request, c, response, _, g
from ckan.controllers.organization import OrganizationController
from ckan.controllers.package import PackageController
from ckan.controllers.user import UserController
from ckan.lib import helpers as h

from ckan.lib.base import abort, render
from ckan.logic import get_action, NotFound, NotAuthorized, check_access, clean_dict, tuplize_dict, parse_params, ValidationError
from paste.deploy.converters import asbool
from pylons import config
import ckan.authz as authz
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.render


from plugin import create_vocabulary

log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
DataError = dictization_functions.DataError

_check_access = check_access
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_


CONTENT_TYPES = {
    'text': 'text/plain;charset=utf-8',
    'html': 'text/html;charset=utf-8',
    'json': 'application/json;charset=utf-8',
    }


class YtpDatasetController(PackageController):
    def ytp_tag_autocomplete(self):
        """ CKAN autocomplete discards vocabulary_id from request.
            This is modification from tag_autocomplete function from CKAN.
            Takes vocabulary_id as parameter.
        """
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        vocabulary_id = request.params.get('vocabulary_id', None)
        if vocabulary_id:
            create_vocabulary(vocabulary_id)

        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session, 'user': c.user or c.author}
            data_dict = {'q': q, 'limit': limit}
            if vocabulary_id:
                data_dict['vocabulary_id'] = vocabulary_id
            try:
                tag_names = get_action('tag_autocomplete')(context, data_dict)
            except NotFound:
                pass  # return empty when vocabulary is not found
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names]
            }
        }

        status_int = 200
        response.status_int = status_int
        response.headers['Content-Type'] = 'application/json;charset=utf-8'
        return h.json.dumps(resultSet)

    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        """ Fake metadata creation. Change status to active and redirect to read. """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        data_dict = get_action('package_show')(context, {'id': id})
        data_dict['id'] = id
        data_dict['state'] = 'active'
        context['allow_state_change'] = True

        get_action('package_update')(context, data_dict)
        success_message = ('<div style="display: inline-block"><p>' + _("Dataset was saved successfully.") + '</p>' +
                           '<p>' + _("Fill additional info") + ':</p>' +
                           '<p><a href="/data/' + h.lang() + '/dataset/' + data_dict.get('name') + '/related/new">>'
                           + _("Add related") + '</a></p>' +
                           '<p><a href="/data/' + h.lang() + '/dataset/edit/' + data_dict.get('name') + '">>'
                           + _("Edit or add language versions") + '</a> ' +
                           '<a href="/data/' + h.lang() + '/dataset/delete/' + id + '">>' + _('Delete') + '</a></p>' +
                           '<p><a href="/data/' + h.lang() + '/dataset/new/">' + _('Create Dataset') + '</a></p></div>')
        h.flash_success(success_message, True)
        h.redirect_to(controller='package', action='read', id=id)

    # Modified from original ckan function
    def edit(self, id, data=None, errors=None, error_summary=None):
        package_type = self._get_package_type(id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        if context['save'] and not data:
            return self._save_edit(id, context, package_type=package_type)
        try:
            c.pkg_dict = get_action('package_show')(context, {'id': id})
            context['for_edit'] = True
            old_data = get_action('package_show')(context, {'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound:
            abort(404, _('Dataset not found'))
        # are we doing a multiphase add?
        if data.get('state', '').startswith('draft') and len(data.get('resources')) == 0:
            c.form_action = h.url_for(controller='package', action='new')
            c.form_style = 'new'
            return self.new(data=data, errors=errors,
                            error_summary=error_summary)

        c.pkg = context.get("package")
        c.resources_json = h.json.dumps(data.get('resources', []))

        try:
            check_access('package_update', context)
        except NotAuthorized:
            abort(401, _('User %r not authorized to edit %s') % (c.user, id))
        # convert tags if not supplied in data
        if data and not data.get('tag_string'):
            data['tag_string'] = ', '.join(h.dict_list_reduce(
                c.pkg_dict.get('tags', {}), 'name'))
        errors = errors or {}
        form_snippet = self._package_form(package_type=package_type)
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary, 'action': 'edit',
                     'dataset_type': package_type,
                     }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)
        c.related_count = c.pkg.related_count

        # we have already completed stage 1
        form_vars['stage'] = ['active']
        if data.get('state', '').startswith('draft') and len(data.get('resources')) == 0:
            form_vars['stage'] = ['active', 'complete']

        edit_template = self._edit_template(package_type)
        c.form = ckan.lib.render.deprecated_lazy_render(
            edit_template,
            form_snippet,
            lambda: render(form_snippet, extra_vars=form_vars),
            'use of c.form is deprecated. please see '
            'ckan/templates/package/edit.html for an example '
            'of the new way to include the form snippet'
        )
        return render(edit_template,
                      extra_vars={'form_vars': form_vars,
                                  'form_snippet': form_snippet,
                                  'dataset_type': package_type})

    # original ckan new resource
    def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']
            resource_id = data['id']
            del data['id']

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if (value or isinstance(value, cgi.FieldStorage)) and key != 'resource_type':
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    h.redirect_to(controller='package',
                                  action='edit', id=id)
                # see if we have added any resources
                try:
                    data_dict = get_action('package_show')(context, {'id': id})
                except NotAuthorized:
                    abort(401, _('Unauthorized to update dataset'))
                except NotFound:
                    abort(404,
                          _('The dataset {id} could not be found.').format(id=id))
                if not len(data_dict['resources']):
                    # no data so keep on page
                    msg = _('You must add at least one data resource')
                    # On new templates do not use flash message
                    if g.legacy_templates:
                        h.flash_error(msg)
                        h.redirect_to(controller='package',
                                      action='new_resource', id=id)
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors, error_summary)
                # we have a resource so let them add metadata
                h.redirect_to(controller='package',
                              action='new_metadata', id=id)

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new_resource(id, data, errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to create a resource'))
            except NotFound:
                abort(404,
                      _('The dataset {id} could not be found.').format(id=id))
            if save_action == 'go-metadata':
                # XXX race condition if another user edits/deletes
                data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                h.redirect_to(controller='package',
                              action='read', id=id)
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                h.redirect_to(controller='package',
                              action='edit', id=id)
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                h.redirect_to(controller='package',
                              action='read', id=id)
            else:
                # add more resources
                h.redirect_to(controller='package',
                              action='new_resource', id=id)

        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access('resource_create', context, {'package_id': pkg_dict['id']})
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource for this package'))

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
        vars['pkg_name'] = id
        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        template = 'package/new_resource_not_draft.html'
        if pkg_dict['state'].startswith('draft') and len(pkg_dict.get('resources')) == 0:
            vars['stage'] = ['complete', 'active']
            template = 'package/new_resource.html'
        return render(template, extra_vars=vars)

    # taken from original ckan resource edit
    def resource_edit(self, id, resource_id, data=None, errors=None,
                      error_summary=None):

        if request.method == 'POST' and not data:
            data = data or clean_dict(unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']

            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to edit this resource'))
            h.redirect_to(controller='package', action='resource_read',
                          id=id, resource_id=resource_id)

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pkg_dict = get_action('package_show')(context, {'id': id})
        if pkg_dict['state'].startswith('draft') and len(pkg_dict.get('resources')) == 0:
            # dataset has not yet been fully created
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
            fields = ['url', 'resource_type', 'format', 'name', 'description', 'id']
            data = {}
            for field in fields:
                data[field] = resource_dict[field]
            return self.new_resource(id, data=data)
        # resource is fully created
        try:
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
        except NotFound:
            abort(404, _('Resource not found'))
        c.pkg_dict = pkg_dict
        c.resource = resource_dict
        # set the form action
        c.form_action = h.url_for(controller='package',
                                  action='resource_edit',
                                  resource_id=resource_id,
                                  id=id)
        if not data:
            data = resource_dict

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
        return render('package/resource_edit.html', extra_vars=vars)

    def new_related(self, id):
        return self._edit_or_new(id, None, False)

    def edit_related(self, id, related_id):
        return self._edit_or_new(id, related_id, True)

    def _edit_or_new(self, id, related_id, is_edit):
        """
        Edit and New were too similar and so I've put the code together
        and try and do as much up front as possible.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

        if is_edit:
            tpl = 'related/edit.html'
            auth_name = 'related_update'
            auth_dict = {'id': related_id}
            action_name = 'related_update'

            try:
                related = get_action('related_show')(
                    context, {'id': related_id})
            except NotFound:
                abort(404, _('Related item not found'))
        else:
            tpl = 'related/new.html'
            auth_name = 'related_create'
            auth_dict = {}
            action_name = 'related_create'

        try:
            check_access(auth_name, context, auth_dict)
        except NotAuthorized:
            abort(401, _('Not authorized'))

        try:
            c.pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('Package not found'))

        data, errors, error_summary = {}, {}, {}

        if request.method == "POST":
            try:
                data = clean_dict(
                    unflatten(
                        tuplize_dict(
                            parse_params(request.params))))

                if is_edit:
                    data['id'] = related_id
                else:
                    data['dataset_id'] = id
                    data['owner_id'] = c.userobj.id

                related = get_action(action_name)(context, data)

                if not is_edit:
                    h.flash_success(_("Related item was successfully created"))
                else:
                    h.flash_success(_("Related item was successfully updated"))

                h.redirect_to(
                    controller='package', action='read', id=c.pkg_dict['name'])
            except DataError:
                abort(400, _(u'Integrity Error'))
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
        else:
            if is_edit:
                data = related

        c.types = self._type_options()

        c.pkg_id = id
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.form = render("related/edit_form.html", extra_vars=vars)
        return render(tpl)

    def _type_options(self):
        '''
        A tuple of options for the different related types for use in
        the form.select() template macro.
        '''
        return ({"text": _("API"), "value": "api"},
                {"text": _("Application"), "value": "application"},
                {"text": _("Idea"), "value": "idea"},
                {"text": _("News Article"), "value": "news_article"},
                {"text": _("Paper"), "value": "paper"},
                {"text": _("Post"), "value": "post"},
                {"text": _("Visualization"), "value": "visualization"})

    def autocomplete_packages_by_collection_type(self, collection_type=None, q=None):

        q = request.params.get('incomplete', '')
        collection_type = request.params.get('collection_type', '')
        limit = request.params.get('limit', None)
        package_dicts = []

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        data_dict = {'q': q, 'limit': limit, 'collection_type': collection_type}

        package_dicts = self._package_autocomplete(context, data_dict)

        resultSet = {'ResultSet': {'Result': package_dicts}}
        return self._finish_ok(resultSet)

    def _package_autocomplete(self, context, data_dict):
        print(data_dict)
        model = context['model']

        _check_access('package_autocomplete', context, data_dict)

        limit = data_dict.get('limit', None)
        q = data_dict.get('q', '')

        like_q = u'%%%s%%' % q

        query = model.Session.query(model.Package)
        query = query.filter(model.Package.state == 'active')
        query = query.filter(model.Package.private == 'False')  # noqa
        query = query.filter(_or_(model.Package.name.ilike(like_q),
                                  model.Package.title.ilike(like_q)))

        collection_type = data_dict.get('collection_type', None)

        if collection_type is not None:
            query = query.join(model.PackageExtra) \
                .filter(_and_(model.PackageExtra.key == 'collection_type'),
                        model.PackageExtra.value == collection_type)

        if limit is not None:
            query = query.limit(limit)
        q_lower = q.lower()
        pkg_list = []
        for package in query:
            if package.name.startswith(q_lower):
                match_field = 'name'
                match_displayed = package.name
            else:
                match_field = 'title'
                match_displayed = '%s (%s)' % (package.title, package.name)
            result_dict = {
                'name': package.name,
                'title': package.title,
                'match_field': match_field,
                'match_displayed': match_displayed}
            pkg_list.append(result_dict)

        return pkg_list

    def _finish(self, status_int, response_data=None,
                content_type='text'):
        '''When a controller method has completed, call this method
        to prepare the response.
        @return response message - return this value from the controller
                                   method
                 e.g. return self._finish(404, 'Package not found')
        '''
        assert(isinstance(status_int, int))
        response.status_int = status_int
        response_msg = ''
        if response_data is not None:
            response.headers['Content-Type'] = CONTENT_TYPES[content_type]
            if content_type == 'json':
                response_msg = h.json.dumps(response_data)
            else:
                response_msg = response_data
            # Support "JSONP" callback.
            if status_int == 200 and 'callback' in request.params and \
                    (request.method == 'GET' or c.logic_function and request.method == 'POST'):
                # escape callback to remove '<', '&', '>' chars
                callback = cgi.escape(request.params['callback'])
                response_msg = self._wrap_jsonp(callback, response_msg)
        return response_msg

    def _finish_ok(self, response_data=None,
                   content_type='json',
                   resource_location=None):
        '''If a controller method has completed successfully then
        calling this method will prepare the response.
        @param resource_location - specify this if a new
           resource has just been created.
        @return response message - return this value from the controller
                                   method
                                   e.g. return self._finish_ok(pkg_dict)
        '''
        if resource_location:
            status_int = 201
            self._set_response_header('Location', resource_location)
        else:
            status_int = 200

        return self._finish(status_int, response_data, content_type)

    def _wrap_jsonp(self, callback, response_msg):
        return '%s(%s);' % (callback, response_msg)

    def _set_response_header(self, name, value):
        try:
            value = str(value)
        except Exception, inst:
            msg = "Couldn't convert '%s' header value '%s' to string: %s" % \
                  (name, value, inst)
            raise Exception(msg)
        response.headers[name] = value


class YtpOrganizationController(OrganizationController):

    def members(self, id):
        group_type = self._ensure_controller_matches_group_type(id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        try:
            data_dict = {'id': id}
            check_access('group_edit_permissions', context, data_dict)
            c.members = self._action('member_list')(
                context, {'id': id, 'object_type': 'user'}
            )
            data_dict['include_datasets'] = False
            c.group_dict = self._action('group_show')(context, {'id': id})

            check_access('group_update', context, {'id': id})
            context['keep_email'] = True
            context['auth_user_obj'] = c.userobj
            context['return_minimal'] = True

            members = []
            for user_id, name, role in c.members:
                user_dict = {'id': user_id}
                data = get_action('user_show')(context, user_dict)
                if data['state'] != 'deleted':
                    members.append((user_id, data['name'], role, data['email']))

            c.members = members
        except NotAuthorized:
            abort(403, _('User %r not authorized to edit members of %s') % (c.user, id))
        except NotFound:
            abort(404, _('Group not found'))
        return self._render_template('group/members.html', group_type)

    def user_list(self):
        if c.userobj and c.userobj.sysadmin:

            q = model.Session.query(model.Group, model.Member, model.User). \
                filter(model.Member.group_id == model.Group.id). \
                filter(model.Member.table_id == model.User.id). \
                filter(model.Member.table_name == 'user'). \
                filter(model.User.name != 'harvest'). \
                filter(model.User.name != 'default'). \
                filter(model.User.state == 'active')

            users = []

            for group, member, user in q.all():
                users.append({
                    'user_id': user.id,
                    'username': user.name,
                    'organization': group.title,
                    'role': member.capacity,
                    'email': user.email
                })

            c.users = users
        else:
            c.users = []

        return self._render_template('group/user_list.html', 'group')

    def admin_list(self):
        if c.userobj and c.userobj.sysadmin:

            q = model.Session.query(model.Group, model.Member, model.User). \
                filter(model.Member.group_id == model.Group.id). \
                filter(model.Member.table_id == model.User.id). \
                filter(model.Member.table_name == 'user'). \
                filter(model.Member.capacity == 'admin'). \
                filter(model.User.name != 'harvest'). \
                filter(model.User.name != 'default'). \
                filter(model.User.state == 'active')

            users = []

            for group, member, user in q.all():
                users.append({
                    'user_id': user.id,
                    'username': user.name,
                    'organization': group.title,
                    'role': member.capacity,
                    'email': user.email
                })

            c.users = users
        else:
            c.users = []

        return self._render_template('group/admin_list.html', 'group')

    def read(self, id, limit=20):
        group_type = self._ensure_controller_matches_group_type(
            id.split('@')[0])
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
                return self._render_template('group/organization_not_found.html', group_type=group_type)

        return OrganizationController.read(self, id, limit)

    def embed(self, id, limit=5):
        """
            Fetch given organization's packages and show them in an embeddable list view.
            See Nginx config for X-Frame-Options SAMEORIGIN header modifications.
        """

        def make_pager_url(q=None, page=None):
            ctrlr = 'ckanext.ytp.controller:YtpOrganizationController'
            url = h.url_for(controller=ctrlr, action='embed', id=id)
            return url + u'?page=' + str(page)

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
                return self._render_template('group/organization_not_found.html')

        page = OrganizationController._get_page_number(self, request.params)

        group_dict = {'id': id}
        group_dict['include_datasets'] = False
        c.group_dict = self._action('group_show')(context, group_dict)
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

        return render("organization/embed.html")


class YtpThemeController(base.BaseController):
    def new_template(self):
        if asbool(config.get('ckanext.ytp.theme.show_postit_demo', True)):
            return render('postit_templates/new.html')
        else:
            return abort(404)

    def return_template(self):
        if asbool(config.get('ckanext.ytp.theme.show_postit_demo', True)):
            return render('postit_templates/return.html')
        else:
            return abort(404)


class YtpUserController(UserController):

    # Modify original CKAN Edit user controller
    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'keep_apikey': True, 'keep_email': True
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        try:
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            abort(403, _('Unauthorized to edit a user.'))

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = \
                    dictization_functions.validate(old_data, schema, context)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(403, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (authz.is_sysadmin(c.user)
                or c.user == user_obj.name):
            abort(403, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user},
                                       data_dict)

        c.is_myself = True
        c.show_email_notifications = asbool(
            config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='user', action='edit',
                      id=user_ref)

    def read(self, id=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj,
                     'include_datasets': True,
                     'include_num_followers': True}

        self._setup_template_variables(context, data_dict)

        # The legacy templates have the user's activity stream on the user
        # profile page, new templates do not.
        if h.asbool(config.get('ckan.legacy_templates', False)):
            c.user_activity_stream = get_action('user_activity_list_html')(
                context, {'id': c.user_dict['id']})

        return render('user/read.html')

    def _save_edit(self, id, context):
        try:
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id

            # MOAN: Do I really have to do this here?
            if 'activity_streams_email_notifications' not in data_dict:
                data_dict['activity_streams_email_notifications'] = False

            get_action('user_update')(context, data_dict)
            h.flash_success(_('Profile updated'))
            h.redirect_to('home')
        except NotAuthorized:
            abort(403, _('Unauthorized to edit user %s') % id)
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)
