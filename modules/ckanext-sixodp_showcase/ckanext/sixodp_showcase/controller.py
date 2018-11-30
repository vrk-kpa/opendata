from ckanext.showcase.controller import ShowcaseController
from ckan.plugins import toolkit as tk
from pylons import config
import ckan
from ckan.controllers.package import search_url, _encode_params
from ckan.common import c, _, request, OrderedDict
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
from urllib import urlencode
from paste.deploy.converters import asbool
import logging

render = tk.render
abort = tk.abort
redirect_to = h.redirect_to
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
NotAuthorized = tk.NotAuthorized


log = logging.getLogger(__name__)


class Sixodp_ShowcaseController(ShowcaseController):

    def manage_showcase_admins(self):
        return super(Sixodp_ShowcaseController, self).manage_showcase_admins()

    def new(self, data=None, errors=None, error_summary=None):
        log.info("In sixodp showcase controller new")
        return super(Sixodp_ShowcaseController, self).new(data=data, errors=errors,
                                                          error_summary=error_summary)

    def _new_template(self, package_type):
        if package_type == 'showcase':
            return "sixodp_showcase/new.html"
        else:
            return super(Sixodp_ShowcaseController, self)._new_template(package_type)

    def read(self, id, format='html'):
        '''
        Detail view for a single showcase, listing its associated datasets.
        '''

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        # check if showcase exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
        except NotFound:
            abort(404, _('Showcase not found'))
        except NotAuthorized:
            abort(404, _('Showcase not found'))

        # get showcase packages
        c.showcase_pkgs = get_action('ckanext_showcase_package_list')(
            context, {'showcase_id': c.pkg_dict['id']})

        return render("sixodp_showcase/read.html",
                      extra_vars={'dataset_type': 'showcase'})

    def edit(self, id, data=None, errors=None, error_summary=None):
        log.info("In sixodp showcase controller edit")
        return super(Sixodp_ShowcaseController, self).edit(id, data=data, errors=errors, error_summary=error_summary)

    def _guess_package_type(self, expecting_name=False):
        """Showcase packages are always DATASET_TYPE_NAME."""
        return 'showcase'

    def _search_template(self, package_type):
        if package_type == 'showcase':
            return "sixodp_showcase/search.html"
        else:
            return super(Sixodp_ShowcaseController, self)._search_template(package_type)

    def _edit_template(self, package_type):
        if package_type == 'showcase':
            return "sixodp_showcase/edit.html"
        else:
            return super(Sixodp_ShowcaseController, self)._edit_template(package_type)

    def search(self):
        from ckan.lib.search import SearchError, SearchQueryError

        package_type = self._guess_package_type()

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

        limit = int(config.get('ckan.datasets_per_page', 20))

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
                                      controller='ckanext.sixodp_showcase.controller:Sixodp_ShowcaseController', action='search')

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
        except SearchQueryError, se:
            # User's search parameters are invalid, in such a way that is not
            # achievable with the web interface, so return a proper error to
            # discourage spiders which are the main cause of this.
            log.info('Dataset search query rejected: %r', se.args)
            abort(400, _('Invalid search query: {error_message}')
                  .format(error_message=str(se)))
        except SearchError, se:
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

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        return render(self._search_template(package_type),
                      extra_vars={'dataset_type': package_type})

    def _package_form(self, package_type=None):
        if package_type == 'showcase':
            return "sixodp_showcase/package_form.html"
        else:
            return super(Sixodp_ShowcaseController, self)._package_form(package_type)
