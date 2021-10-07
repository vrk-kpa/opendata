# -*- coding: utf-8 -*-

from flask import Blueprint

import ckantoolkit as tk
from ckan.common import c, _, request
from collections import OrderedDict
from ckan.plugins.toolkit import config, asbool
import ckan.lib.helpers as h
import ckan.views.dataset as dataset
from ckan.controllers.package import search_url, _encode_params
from urllib import urlencode
import ckan

import ckan.model as model
import ckanext.showcase.utils as utils
import ckanext.showcase.views as views
render = tk.render
abort = tk.abort
redirect_to = h.redirect_to
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
import logging
log = logging.getLogger(__name__)



def index():
    from ckan.lib.search import SearchError, SearchQueryError

    package_type = utils.DATASET_TYPE_NAME

    try:
        context = {'model': model, 'user': c.user,
                    'auth_user_obj': c.userobj}
        check_access('site_read', context)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    # unicode format (decoded from utf8)
    q = c.q = request.params.get('q', u'')
    c.query_error = False
    page = h.get_page_number(request.params)

    limit = int(config.get('ckan.datasets_per_page', 21))

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in request.params.items()
                        if k != 'page']

    def drill_down_url(alternative_url=None, **by):
        return h.add_url_param(alternative_url=alternative_url,
                                controller='ckanext.sixodp_showcase.controller:Sixodp_ShowcaseController', action='search',
                                new_params=by)

    c.drill_down_url = drill_down_url

    def remove_field(key, value=None, replace=None):
        return h.remove_url_param(key, value=value, replace=replace,
                                    controller='ckanext.sixodp_showcase.controller:Sixodp_ShowcaseController',
                                    action='search')

    c.remove_field = remove_field

    sort_by = request.params.get('sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

    def _sort_by(fields):
        """
        Sort by the given list of fields.
        Each entry in the list is a 2-tuple: (fieldname, sort_order)
        eg - [('metadata_modified', 'desc'), ('name', 'asc')]
        If fields is empty, then the default ordering is used.
        """
        params = params_nosort[:]

        if fields:
            sort_string = ', '.join('%s %s' % f for f in fields)
            params.append(('sort', sort_string))
        return search_url(params, package_type)

    c.sort_by = _sort_by
    if not sort_by:
        c.sort_by_fields = []
    else:
        c.sort_by_fields = [field.split()[0]
                            for field in sort_by.split(',')]

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append(('page', page))
        return search_url(params, package_type)

    c.search_url_params = urlencode(_encode_params(params_nopage))

    try:
        c.fields = []
        # c.fields_grouped will contain a dict of params containing
        # a list of values eg {'tags':['tag1', 'tag2']}
        c.fields_grouped = {}
        search_extras = {}
        fq = ''
        for (param, value) in request.params.items():
            if param not in ['q', 'page', 'sort'] \
                    and len(value) and not param.startswith('_'):
                if not param.startswith('ext_'):
                    c.fields.append((param, value))
                    fq += ' %s:"%s"' % (param, value)
                    if param not in c.fields_grouped:
                        c.fields_grouped[param] = [value]
                    else:
                        c.fields_grouped[param].append(value)
                else:
                    search_extras[param] = value

        context = {'model': model, 'session': model.Session,
                    'user': c.user, 'for_view': True,
                    'auth_user_obj': c.userobj}

        if package_type and package_type != 'dataset':
            # Only show datasets of this particular type
            fq += ' +dataset_type:{type}'.format(type=package_type)
        else:
            # Unless changed via config options, don't show non standard
            # dataset types on the default search page
            if not asbool(
                    config.get('ckan.search.show_all_types', 'False')):
                fq += ' +dataset_type:dataset'

        facets = OrderedDict()

        default_facet_titles = {
            'organization': _('Organizations'),
            'groups': _('Groups'),
            'tags': _('Tags'),
            'res_format': _('Formats'),
            'license_id': _('Licenses'),
        }

        for facet in h.facets():
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        for plugin in ckan.plugins.PluginImplementations(ckan.plugins.IFacets):
            facets = plugin.dataset_facets(facets, package_type)

        c.facet_titles = facets

        # Set the custom default sort parameter here
        # Might need a rewrite when ckan is updated
        if not sort_by:
            sort_by = 'metadata_created desc'

        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': facets.keys(),
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras,
            'include_private': asbool(config.get(
                'ckan.search.default_include_private', True)),
        }

        query = get_action('package_search')(context, data_dict)
        c.sort_by_selected = query['sort']

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )
        c.facets = query['facets']
        c.search_facets = query['search_facets']
        c.page.items = query['results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info('Dataset search query rejected: %r', se.args)
        abort(400, _('Invalid search query: {error_message}')
                .format(error_message=str(se)))
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error('Dataset search error: %r', se.args)
        c.query_error = True
        c.facets = {}
        c.search_facets = {}
        c.page = h.Page(collection=[])
    c.search_facets_limits = {}
    for facet in c.search_facets.keys():
        try:
            limit = int(request.params.get('_%s_limit' % facet,
                                            int(config.get('search.facets.default', 10))))
        except ValueError:
            abort(400, _('Parameter "{parameter_name}" is not '
                            'an integer').format(
                parameter_name='_%s_limit' % facet))
        c.search_facets_limits[facet] = limit

    # self._setup_template_variables(context, {},
    #                                 package_type=package_type)

    return render("sixodp_showcase/search.html",
                    extra_vars={'dataset_type': package_type})


class CreateView(dataset.CreateView):
    def get(self, data=None, errors=None, error_summary=None):
        utils.check_new_view_auth()
        return super(CreateView, self).get(utils.DATASET_TYPE_NAME, data,
                                           errors, error_summary)

    def post(self):

        data_dict = dataset.clean_dict(
            dataset.dict_fns.unflatten(
                dataset.tuplize_dict(dataset.parse_params(tk.request.form))))
        data_dict.update(
            dataset.clean_dict(
                dataset.dict_fns.unflatten(
                    dataset.tuplize_dict(dataset.parse_params(
                        tk.request.files)))))
        context = self._prepare()
        data_dict['type'] = utils.DATASET_TYPE_NAME
        context['message'] = data_dict.get('log_message', '')

        try:
            pkg_dict = tk.get_action('ckanext_showcase_create')(context,
                                                                data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            data_dict['state'] = 'none'
            return self.get(data_dict, errors, error_summary)

        # redirect to manage datasets
        url = h.url_for('showcase_blueprint.manage_datasets',
                        id=pkg_dict['name'])
        return h.redirect_to(url)


def manage_datasets(id):
    return utils.manage_datasets_view(id)


def delete(id):
    return utils.delete_view(id)


def read(id):
    return utils.read_view(id)


class EditView(dataset.EditView):
    def get(self, id, data=None, errors=None, error_summary=None):
        utils.check_new_view_auth()
        return super(EditView, self).get(utils.DATASET_TYPE_NAME, id, data,
                                         errors, error_summary)

    def post(self, id):
        context = self._prepare(id)
        utils.check_edit_view_auth(id)

        data_dict = dataset.clean_dict(
            dataset.dict_fns.unflatten(
                dataset.tuplize_dict(dataset.parse_params(tk.request.form))))
        data_dict.update(
            dataset.clean_dict(
                dataset.dict_fns.unflatten(
                    dataset.tuplize_dict(dataset.parse_params(
                        tk.request.files)))))

        data_dict['id'] = id
        try:
            pkg = tk.get_action('ckanext_showcase_update')(context, data_dict)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        tk.c.pkg_dict = pkg

        # redirect to showcase details page
        url = h.url_for('showcase_blueprint.read', id=pkg['name'])
        return h.redirect_to(url)


def dataset_showcase_list(id):
    return utils.dataset_showcase_list(id)


def admins():
    return utils.manage_showcase_admins()


def admin_remove():
    return utils.remove_showcase_admin()


def upload():
    return utils.upload()

showcase = Blueprint(u'sixodp_showcase', __name__)

showcase.add_url_rule('/showcase', view_func=index)
# showcase.add_url_rule('/showcase/new', view_func=CreateView.as_view('new'))
# showcase.add_url_rule('/showcase/delete/<id>',
#                       view_func=delete,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/showcase/<id>', view_func=read)
# showcase.add_url_rule('/showcase/edit/<id>',
#                       view_func=EditView.as_view('edit'),
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/showcase/manage_datasets/<id>',
#                       view_func=manage_datasets,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/dataset/showcases/<id>',
#                       view_func=dataset_showcase_list,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/ckan-admin/showcase_admins',
#                       view_func=admins,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/ckan-admin/showcase_admin_remove',
#                       view_func=admin_remove,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/showcase_upload',
#                       view_func=upload,
#                       methods=[u'POST'])


def get_blueprints():
    return [showcase] + views.get_blueprints()