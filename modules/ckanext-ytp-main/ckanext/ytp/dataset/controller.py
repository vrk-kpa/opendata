from ckan import model
from ckan.common import request, c, response, _
from ckan.logic import get_action, NotFound, NotAuthorized, check_access
from ckan.lib import helpers
from ckan.controllers.package import PackageController
from ckan.lib.base import redirect, abort, render

from pylons import config

h = helpers


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
                           '<p><a href="/data/dataset/' + data_dict.get('name') + '/related/new">>' + _("Add related") + '</a></p>' +
                           '<p><a href="/data/dataset/edit/' + data_dict.get('name') + '">>' + _("Edit or add language versions") + '</a> ' +
                           '<a href="/data/dataset/delete/' + id + '">>' + _('Delete') + '</a></p>' +
                           '<p><a href="/data/dataset/new/">' + _('Create Dataset') + '</a></p></div>')
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
        from pprint import pprint
        pprint(data.get('resources'))
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
