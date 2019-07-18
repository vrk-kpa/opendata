import logging

import ckan.lib.base as base
from helpers import advancedsearch_schema, query_helper
from ckan.common import c, request
from ckan.lib import helpers as h
from ckan.lib.base import render
from ckan.logic import get_action

log = logging.getLogger(__name__)


class YtpAdvancedSearchController(base.BaseController):
    def search(self):
        from ckan import model

        schema = advancedsearch_schema()
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user
        }

        # TODO: get the page from the url
        page = 1
        limit = 2
        search_query_filters = []
        q = ''
        main_query_field = schema['main_query_field']

        if request.method == 'POST':
            main_query_helper = query_helper(schema['input_fields'].get(main_query_field))
            q = main_query_helper(main_query_field, request.POST, schema['input_fields'], context)
            # Iterate through all fields in schema except the main_query_field
            # and process every field with the provided query_helper
            for key, val in schema['input_fields'].iteritems():
                # Skip field used for main query
                if key == main_query_field:
                    continue
                # Get query helper function from schema
                query_helper_function = query_helper(val)
                # TODO: handle no query_helper
                if query_helper_function:
                    res = query_helper_function(key, request.POST, schema['input_fields'], context)
                    if res:
                        search_query_filters.append(res)

        data_dict = {
            'q': q,
            'rows': limit,
            'start': (page - 1) * limit,
            'extras': {}
        }

        if search_query_filters:
            data_dict['fq'] = '(' + ') AND ('.join(search_query_filters) + ')'

        query = get_action('package_search')(context, data_dict)

        def make_pager_url(q=None, page=None):
            ctrlr = 'ckanext.advancedsearch.controller:YtpAdvancedSearchController'
            url = h.url_for(controller=ctrlr, action='search')
            return url + u'?page=' + str(page)

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=make_pager_url,
            item_count=query['count'],
            items_per_page=limit
        )

        c.page.items = query['results']
        return render('advanced_search/index.html')
