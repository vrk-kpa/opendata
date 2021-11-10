import json
import logging
import math

from ckan.common import c, request
from ckan.lib.base import render
from ckan.logic import get_action
from flask import Blueprint

from .helpers import advancedsearch_schema, field_options, query_helper


log = logging.getLogger(__name__)
bp_search = Blueprint('advanced_search_blueprint', __name__)


def get_blueprints():
    return [
        bp_search,
    ]


@bp_search.route('/advanced_search', methods=['GET', 'POST'])
def search():
    from ckan import model
    schema = advancedsearch_schema()

    context = {
        'model': model,
        'session': model.Session,
        'user': c.user
    }

    # On initial page load there is no page parameter so display the first page
    # On possible page navigations use the page parameter to move to the next page
    # NOTE: this works also with a GET request but the POST filters will not be submitted so all datasets will be returned
    page = int(request.params.get('page', 1))
    # Limit amount of results returned
    limit = 20
    search_query_filters = []
    q = ''
    main_query_field = schema['main_query_field']

    options = {}

    for key, val in schema['input_fields'].items():
        # Skip field used for main query
        if key == main_query_field:
            continue

        # Make a list of field options
        options[key] = field_options(val)

    if request.method == 'POST':
        # Use the field labelled as the main_query to build the value for q
        # TODO: Handle no main_query_field provided
        main_query_helper = query_helper(schema['input_fields'].get(main_query_field))
        q = main_query_helper(main_query_field, request.form, schema['input_fields'], context)

        # Iterate through all fields in schema except the main_query_field
        # and process every field with the provided query_helper
        for key, val in schema['input_fields'].items():
            # Skip field used for main query
            if key == main_query_field:
                continue
            # Get query helper function from schema
            query_helper_function = query_helper(val)
            # TODO: handle no query_helper
            if query_helper_function:
                res = query_helper_function(key, request.form, schema['input_fields'], context)
                if res:
                    search_query_filters.append(res)

    sort_string = request.form.get('sort', 'metadata_created desc')

    data_dict = {
        'q': q,
        'rows': limit,
        'start': (page - 1) * limit,
        'extras': {},
        'sort': sort_string,
        'defType': 'edismax',
        'mm': 0
    }

    if search_query_filters:
        # Outputs: (filter:value) AND (another_filter:another_value)
        data_dict['fq'] = '(' + ') AND ('.join(search_query_filters) + ')'

    query = get_action('package_search')(context, data_dict)

    json_query = json.dumps(
        {k: v for k, v in list(params_to_dict(request.form).items()) if k != 'page' and type(v) is list and len(v[0]) > 0}
    )

    filters = {
        k: v for k, v in list(params_to_dict(request.form).items()) if k != 'search_target' and k != 'search_query'
        and k != 'page' and k != 'released-before' and k != 'released-after' and k != 'updated-before'
        and k != 'updated-after' and k != 'sort' and type(v) is list and len(v[0]) > 0
    }

    for key, value in filters.items():
        if 'all' in value:
            filters[key] = [{'value': 'all', 'label': 'All'}]
            continue
        if options and options[key]:
            options_list = []
            for option in value:
                x = next((x for x in options[key] if x.get('value') == option), None)
                if x:
                    options_list.append(x)
            filters[key] = options_list

    c.advanced_search = {
        "item_count": query['count'],
        # Round values up to get total amount of pages
        "total_pages": int(math.ceil(float(query['count']) / float(limit))),
        "collection": query['results'],
        # Return query parameters to the UI so that it can populate the fields with the previous query values
        # NOTE: Can this cause security issues? Returning POST request params back to the client
        "last_query": params_to_dict(request.form),
        "json_query": json_query,
        "filters": filters,
        "sort_string": sort_string,
        "field_options": options
        }
    c.advanced_search['last_query']['page'] = page

    return render('advanced_search/index.html')


def params_to_dict(params):
    new_dict = {}
    for i in params:
        key = i
        if not hasattr(new_dict, key):
            value = params.getlist(i)
            new_dict.setdefault(key, value)
    return new_dict
