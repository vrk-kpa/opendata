import logging
from collections import OrderedDict
import ckantoolkit as toolkit
import ckan.views.dataset as dataset
from functools import partial
from urllib.parse import urlencode
from ckan import model

import ckan.plugins as plugins
import ckan.logic as logic
from ckan.plugins.toolkit import g, config, request, _, asbool
import ckan.lib.helpers as h
from ckan.lib.search import SearchError, SearchQueryError
from ckanext.showcase import utils as showcase_utils
from ckanext.sixodp_showcase.model import ShowcaseApisetAssociation


NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
_encode_params = dataset._encode_params
c = toolkit.c

log = logging.getLogger(__name__)


def drill_down_url(alternative_url=None, **by):
    return h.add_url_param(
        alternative_url=alternative_url,
        controller=u'sixodp_showcase',
        action=u'search',
        new_params=by
    )


def remove_field(package_type, key, value=None, replace=None):
    url = h.url_for(u'sixodp_showcase.search')
    return h.remove_url_param(
        key,
        value=value,
        replace=replace,
        alternative_url=url
    )


def _add_apiset_search(showcase_id, showcase_name):
    '''
    Search logic for discovering apisets to add to a showcase.
    '''

    from ckan.lib.search import SearchError

    package_type = 'apiset'
    # unicode format (decoded from utf8)
    q = c.q = toolkit.request.params.get('q', u'')
    c.query_error = False
    page = h.get_page_number(toolkit.request.params)

    limit = int(toolkit.config.get('ckan.datasets_per_page', 20))

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in toolkit.request.params.items()
                     if k != 'page']

    def drill_down_url(alternative_url=None, **by):
        return h.add_url_param(alternative_url=alternative_url,
                               controller=package_type
                               if toolkit.check_ckan_version('2.9') else 'package',
                               action='search',
                               new_params=by)

    c.drill_down_url = drill_down_url

    def remove_field(key, value=None, replace=None):
        return h.remove_url_param(key,
                                  value=value,
                                  replace=replace,
                                  controller=package_type,
                                  action='search')

    c.remove_field = remove_field

    sort_by = toolkit.request.params.get('sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

    def _search_url(params, name):
        url = h.url_for('sixodp_showcase_manage_apisets', id=name)
        return url_with_params(url, params)

    def url_with_params(url, params):
        params = _encode_params(params)
        return url + u'?' + urlencode(params)

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
        return _search_url(params, showcase_name)

    c.sort_by = _sort_by
    if sort_by is None:
        c.sort_by_fields = []
    else:
        c.sort_by_fields = [field.split()[0] for field in sort_by.split(',')]

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append(('page', page))
        return _search_url(params, showcase_name)

    c.search_url_params = urlencode(_encode_params(params_nopage))

    try:
        c.fields = []
        # c.fields_grouped will contain a dict of params containing
        # a list of values eg {'tags':['tag1', 'tag2']}
        c.fields_grouped = {}
        search_extras = {}
        fq = ''
        for (param, value) in toolkit.request.params.items():
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

        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'for_view': True,
            'auth_user_obj': c.userobj
        }

        if package_type and package_type != 'dataset':
            # Only show datasets of this particular type
            fq += ' +dataset_type:{type}'.format(type=package_type)
        else:
            # Unless changed via config options, don't show non standard
            # dataset types on the default search page
            if not toolkit.asbool(
                    toolkit.config.get('ckan.search.show_all_types', 'False')):
                fq += ' +dataset_type:dataset'

        # Only search for packages that aren't already associated with the
        # Showcase
        associated_package_ids = ShowcaseApisetAssociation.get_apiset_ids_for_showcase(
            showcase_id)
        # flatten resulting list to space separated string
        if associated_package_ids:
            associated_package_ids_str = \
                ' OR '.join([id[0] for id in associated_package_ids])
            fq += ' !id:({0})'.format(associated_package_ids_str)

        facets = OrderedDict()

        default_facet_titles = {
            'organization': _('Organizations'),
            'groups': _('Groups'),
            'tags': _('Tags'),
            'res_format': _('Formats'),
            'license_id': _('Licenses'),
        }

        # for CKAN-Versions that do not provide the facets-method from
        # helper-context, import facets from ckan.common
        if hasattr(h, 'facets'):
            current_facets = h.facets()
        else:
            from ckan.common import g
            current_facets = g.facets

        for facet in current_facets:
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        for plugin in plugins.PluginImplementations(plugins.IFacets):
            facets = plugin.dataset_facets(facets, package_type)

        c.facet_titles = facets

        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': list(facets.keys()),
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras
        }

        query = toolkit.get_action('package_search')(context, data_dict)
        c.sort_by_selected = query['sort']

        c.page = h.Page(collection=query['results'],
                        page=page,
                        url=pager_url,
                        item_count=query['count'],
                        items_per_page=limit)
        c.facets = query['facets']
        c.search_facets = query['search_facets']
        c.page.items = query['results']
    except SearchError as se:
        log.error('Dataset search error: %r', se.args)
        c.query_error = True
        c.facets = {}
        c.search_facets = {}
        c.page = h.Page(collection=[])
    c.search_facets_limits = {}
    for facet in c.search_facets.keys():
        try:
            limit = int(
                toolkit.request.params.get(
                    '_%s_limit' % facet,
                    int(toolkit.config.get('search.facets.default', 10))))
        except toolkit.ValueError:
            toolkit.abort(
                400,
                _("Parameter '{parameter_name}' is not an integer").format(
                    parameter_name='_%s_limit' % facet))
        c.search_facets_limits[facet] = limit


def index(package_type):
    extra_vars = {}

    try:
        context = {
            u'model': model,
            u'user': g.user,
            u'auth_user_obj': g.userobj
        }
        check_access(u'site_read', context)
    except NotAuthorized:
        toolkit.abort(403, _(u'Not authorized to see this page'))

    # unicode format (decoded from utf8)
    extra_vars[u'q'] = q = request.args.get(u'q', u'')

    extra_vars['query_error'] = False
    page = h.get_page_number(request.args)

    limit = int(config.get(u'ckan.datasets_per_page', 21))

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    extra_vars[u'drill_down_url'] = drill_down_url
    extra_vars[u'remove_field'] = partial(remove_field, package_type)

    sort_by = request.args.get(u'sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    extra_vars[u'sort_by'] = partial(dataset._sort_by, params_nosort, package_type)

    if not sort_by:
        sort_by_fields = []
    else:
        sort_by_fields = [field.split()[0] for field in sort_by.split(u',')]
    extra_vars[u'sort_by_fields'] = sort_by_fields

    pager_url = partial(dataset._pager_url, params_nopage, package_type)

    search_url_params = urlencode(_encode_params(params_nopage))
    extra_vars[u'search_url_params'] = search_url_params

    details = dataset._get_search_details()
    extra_vars[u'fields'] = details[u'fields']
    extra_vars[u'fields_grouped'] = details[u'fields_grouped']
    fq = details[u'fq']
    search_extras = details[u'search_extras']

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    # Unless changed via config options, don't show other dataset
    # types any search page. Potential alternatives are do show them
    # on the default search page (dataset) or on one other search page
    search_all_type = config.get(u'ckan.search.show_all_types', u'dataset')
    search_all = False

    try:
        # If the "type" is set to True or False, convert to bool
        # and we know that no type was specified, so use traditional
        # behaviour of applying this only to dataset type
        search_all = asbool(search_all_type)
        search_all_type = u'dataset'
    # Otherwise we treat as a string representing a type
    except ValueError:
        search_all = True

    if not search_all or package_type != search_all_type:
        # Only show datasets of this particular type
        fq += u' +dataset_type:{type}'.format(type=package_type)

    facets = OrderedDict()

    default_facet_titles = {
        u'organization': _(u'Organizations'),
        u'groups': _(u'Groups'),
        u'tags': _(u'Tags'),
        u'res_format': _(u'Formats'),
        u'license_id': _(u'Licenses'),
    }

    for facet in h.facets():
        if facet in default_facet_titles:
            facets[facet] = default_facet_titles[facet]
        else:
            facets[facet] = facet

    # Facet titles
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.dataset_facets(facets, package_type)

    extra_vars[u'facet_titles'] = facets
    data_dict = {
        u'q': q,
        u'fq': fq.strip(),
        u'facet.field': list(facets.keys()),
        u'rows': limit,
        u'start': (page - 1) * limit,
        u'sort': sort_by,
        u'extras': search_extras,
        u'include_private': asbool(
            config.get(u'ckan.search.default_include_private', True)
        ),
    }
    try:
        query = get_action(u'package_search')(context, data_dict)

        extra_vars[u'sort_by_selected'] = sort_by
        g.sort_by_selected = sort_by

        extra_vars[u'page'] = h.Page(
            collection=query[u'results'],
            page=page,
            url=pager_url,
            item_count=query[u'count'],
            items_per_page=limit
        )
        extra_vars[u'search_facets'] = query[u'search_facets']
        g.search_facets = query['search_facets']
        g.facets = query[u'facets']
        extra_vars[u'page'].items = query[u'results']
    except SearchQueryError as se:
        # User's search parameters are invalid, in such a way that is not
        # achievable with the web interface, so return a proper error to
        # discourage spiders which are the main cause of this.
        log.info(u'Dataset search query rejected: %r', se.args)
        toolkit.abort(
            400,
            _(u'Invalid search query: {error_message}')
            .format(error_message=str(se))
        )
    except SearchError as se:
        # May be bad input from the user, but may also be more serious like
        # bad code causing a SOLR syntax error, or a problem connecting to
        # SOLR
        log.error(u'Dataset search error: %r', se.args)
        extra_vars[u'query_error'] = True
        g.facets = {}
        extra_vars[u'search_facets'] = {}
        extra_vars[u'page'] = h.Page(collection=[])

    g.search_facets_limits = {}
    for facet in extra_vars[u'search_facets'].keys():
        try:
            limit = int(
                request.args.get(
                    u'_%s_limit' % facet,
                    int(config.get(u'search.facets.default', 10))
                )
            )
        except ValueError:
            toolkit.abort(
                400,
                _(u'Parameter u"{parameter_name}" is not '
                  u'an integer').format(parameter_name=u'_%s_limit' % facet)
            )
        g.search_facets_limits[facet] = limit

    dataset._setup_template_variables(context, {}, package_type=package_type)

    extra_vars[u'dataset_type'] = package_type

    return toolkit.render(
        'sixodp_showcase/search.html', extra_vars
    )


def read(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': c.user or c.author,
        'for_view': True,
        'auth_user_obj': c.userobj
    }
    data_dict = {'id': id}

    # check if showcase exists
    try:
        c.pkg_dict = toolkit.get_action('package_show')(context, data_dict)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Showcase not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized to read showcase'))

    # get showcase packages
    c.showcase_pkgs = toolkit.get_action('ckanext_showcase_package_list')(
        context, {
            'showcase_id': c.pkg_dict['id']
        })

    package_type = showcase_utils.DATASET_TYPE_NAME
    return toolkit.render('sixodp_showcase/read.html',
                          extra_vars={'dataset_type': package_type})


def manage_apisets_view(id):

    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user or toolkit.c.author
    }
    data_dict = {'id': id}

    try:
        toolkit.check_access('ckanext_showcase_update', context)
    except toolkit.NotAuthorized:
        return toolkit.abort(
            401,
            _('User not authorized to edit {showcase_id}').format(
                showcase_id=id))

    # check if showcase exists
    try:
        toolkit.c.pkg_dict = toolkit.get_action('package_show')(context, data_dict)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Showcase not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized to read showcase'))

    # Are we removing a showcase/apiset association?
    form_data = toolkit.request.form

    manage_route = 'sixodp_showcase.manage_apisets'

    if (toolkit.request.method == 'POST'
            and 'bulk_action.showcase_remove' in form_data):
        # Find the apisets to perform the action on, they are prefixed by
        # apiset_ in the form data
        package_ids = []
        for param in form_data:
            if param.startswith('apiset_'):
                package_ids.append(param[7:])
        if package_ids:
            for package_id in package_ids:
                toolkit.get_action('ckanext_sixodp_showcase_apiset_association_delete')(
                    context, {
                        'showcase_id': toolkit.c.pkg_dict['id'],
                        'package_id': package_id
                    })
            h.flash_success(
                toolkit.ungettext(
                    "The apiset has been removed from the showcase.",
                    "The apisets have been removed from the showcase.",
                    len(package_ids)))
            url = h.url_for(manage_route, id=id)
            return h.redirect_to(url)

    # Are we creating a showcase/apiset association?
    elif (toolkit.request.method == 'POST'
          and 'bulk_action.showcase_add' in form_data):
        # Find the apisets to perform the action on, they are prefixed by
        # apiset_ in the form data
        package_ids = []
        for param in form_data:
            if param.startswith('apiset_'):
                package_ids.append(param[7:])
        if package_ids:
            successful_adds = []
            for package_id in package_ids:
                try:
                    toolkit.get_action(
                        'ckanext_sixodp_showcase_apiset_association_create')(
                            context, {
                                'showcase_id': toolkit.c.pkg_dict['id'],
                                'package_id': package_id
                            })
                except toolkit.ValidationError as e:
                    h.flash_notice(e.error_summary)
                else:
                    successful_adds.append(package_id)
            if successful_adds:
                h.flash_success(
                    toolkit.ungettext(
                        "The apiset has been added to the showcase.",
                        "The apisets have been added to the showcase.",
                        len(successful_adds)))
            url = h.url_for(manage_route, id=id)
            return h.redirect_to(url)

    _add_apiset_search(toolkit.c.pkg_dict['id'], toolkit.c.pkg_dict['name'])

    # get showcase packages
    toolkit.c.showcase_pkgs = toolkit.get_action('ckanext_sixodp_showcase_apiset_list')(
        context, {
            'showcase_id': toolkit.c.pkg_dict['id']
        })

    return toolkit.render('showcase/manage_apisets.html', extra_vars={
        'view_type': 'manage_apisets',
    })
