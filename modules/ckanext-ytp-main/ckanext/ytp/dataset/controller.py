import cgi
from ckan import model
from ckan.common import request, c, response, _, g
from ckan.controllers.package import PackageController
from ckan.lib import helpers
from ckan.lib.base import redirect, abort, render
import ckan.lib.render
from ckan.logic import get_action, NotFound, NotAuthorized, check_access, clean_dict, parse_params, tuplize_dict, ValidationError

from pylons import config

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.package_saver as package_saver
from genshi.template import MarkupTemplate

import sqlalchemy

_check_access = check_access
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_


h = helpers

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
        return helpers.json.dumps(resultSet)

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
                           '<p><a href="/data/' + h.lang() + '/dataset/' + data_dict.get('name') + '/related/new">>' + _("Add related") + '</a></p>' +
                           '<p><a href="/data/' + h.lang() + '/dataset/edit/' + data_dict.get('name') + '">>' + _("Edit or add language versions") + '</a> ' +
                           '<a href="/data/' + h.lang() + '/dataset/delete/' + id + '">>' + _('Delete') + '</a></p>' +
                           '<p><a href="/data/' + h.lang() + '/dataset/new/">' + _('Create Dataset') + '</a></p></div>')
        helpers.flash_success(success_message, True)
        redirect(helpers.url_for(controller='package', action='read', id=id))

    # Modified from original ckan function
    def edit(self, id, data=None, errors=None, error_summary=None):
        package_type = self._get_package_type(id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params,
                   'moderated': config.get('moderated'),
                   'pending': True}

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
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'edit'}
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)
        c.related_count = c.pkg.related_count

        # we have already completed stage 1
        vars['stage'] = ['active']
        if data.get('state', '').startswith('draft'):
            vars['stage'] = ['active', 'complete']

        # TODO: This check is to maintain backwards compatibility with the
        # old way of creating custom forms. This behaviour is now deprecated.
        if hasattr(self, 'package_form'):
            c.form = render(self.package_form, extra_vars=vars)
        else:
            c.form = render(self._package_form(package_type=package_type),
                            extra_vars=vars)

        return render(self._edit_template(package_type),
                      extra_vars={'stage': vars['stage']})

    # original ckan new resource
    def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
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
                if ((value or isinstance(value, cgi.FieldStorage)) and key != 'resource_type'):
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    redirect(h.url_for(controller='package',
                                       action='edit', id=id))
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
                        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors, error_summary)
                # we have a resource so let them add metadata
                redirect(h.url_for(controller='package',
                                   action='new_metadata', id=id))

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
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        vars['pkg_name'] = id
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
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
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
            redirect(h.url_for(controller='package', action='resource_read',
                               id=id, resource_id=resource_id))

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

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        return render('package/resource_edit.html', extra_vars=vars)

    def read(self, id, format='html'):
        ''' Copied and overriden from CKAN's package controller '''

        if not format == 'html':
            ctype, extension, loader = \
                self._content_type_from_extension(format)
            if not ctype:
                # An unknown format, we'll carry on in case it is a
                # revision specifier and re-constitute the original id
                id = "%s.%s" % (id, format)
                ctype, format, loader = "text/html; charset=utf-8", "html", \
                    MarkupTemplate
        else:
            ctype, format, loader = self._content_type_from_accept()

        response.headers['Content-Type'] = ctype

        package_type = self._get_package_type(id.split('@')[0])
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        # interpret @<revision_id> or @<date> suffix
        split = id.split('@')
        if len(split) == 2:
            data_dict['id'], revision_ref = split
            if model.is_id(revision_ref):
                context['revision_id'] = revision_ref
            else:
                try:
                    date = h.date_str_to_datetime(revision_ref)
                    context['revision_date'] = date
                except TypeError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
                except ValueError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
        elif len(split) > 2:
            abort(400, _('Invalid revision format: %r') %
                  'Too many "@" symbols')

        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = c.pkg.related_count

        # Added the related items so that we have access to them in the template
        c.related_list = get_action('related_list')(context, data_dict)

        # can the resources be previewed?
        for resource in c.pkg_dict['resources']:
            resource['can_be_previewed'] = self._resource_preview(
                {'resource': resource, 'package': c.pkg_dict})

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        package_saver.PackageSaver().render_package(c.pkg_dict, context)

        template = self._read_template(package_type)
        template = template[:template.index('.') + 1] + format

        try:
            return render(template, loader_class=loader)
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(package_type=package_type,
                                                                             format=format, file=template))
            abort(404, msg)

        assert False, "We should never get here"

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
                    dict_fns.unflatten(
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
            except dict_fns.DataError:
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
