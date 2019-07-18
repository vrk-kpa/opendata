from ckan.logic import get_action

# TODO: Should not be cross dependant to ckanext.ytp
# This is specific to ytp
from ckanext.ytp.helpers import get_translated

import logging

log = logging.getLogger(__name__)


def field_options(field):
    """
    :param field: scheming field definition
    :returns: options iterable or None if not found.
    """
    if 'options' in field:
        return field['options']
    if 'options_helper' in field:
        from ckantoolkit import h
        options_fn = getattr(h, field['options_helper'])
        return options_fn(field)


def query_helper(field):
    """
    :param field: scheming field definition
    :returns: options iterable or None if not found.
    """
    if 'query_helper' in field:
        from ckantoolkit import h
        query_helper = field['query_helper']
        if '(' in query_helper and query_helper[-1] == ')':
            name, args = query_helper.split('(', 1)
            args = args[:-1].split(',')  # trim trailing ')', break up
            return getattr(h, name)(*args)
        else:
            return getattr(h, query_helper)()
        

def advancedsearch_schema():
    """
    Return the dict of dataset schemas. Or if scheming_datasets
    plugin is not loaded return None.
    """
    from ckanext.advancedsearch.plugin import AdvancedsearchPlugin as p
    if p.instance:
        return p.instance._schema


# OPTIONS
# NOTE: these are a bit ytp specific, these could be defined where the search_fields are
def advanced_category_options(field=None):
    from ckan import model

    context = {'model': model, 'session': model.Session}
    groups = get_action('group_list')(context, {})

    options = []
    for group in groups:
        group_details = get_action('group_show')(context, {"id": group})
        options.append({"value": group_details['display_name'], "label": get_translated(group_details, 'title')})

    return options


def advanced_publisher_options(field=None):
    from ckan import model
    import ckan.plugins as p

    context = {'model': model, 'session': model.Session}
    publishers = p.toolkit.get_action('get_organizations')(context, {})

    return make_options(publishers)


def advanced_license_options(field=None):
    from ckan import model
    context = {'model': model, 'session': model.Session}

    licenses = get_action('license_list')(context)

    return make_options(licenses)


def advanced_format_options(field=None):
    from ckan import model
    context = {'model': model, 'session': model.Session}

    formats = get_action('get_formats')(context)

    options = []
    for item in formats:
        options.append({"value": item.lower(), "label": item})

    return options


def make_options(items, value='id', label="title", has_translated=False):
    options = []
    for item in items:
        options.append({
            "value": item[value],
            "label": get_translated(item, label) if has_translated else item[label]
        })

    return options


# QUERY HELPERS
def advanced_multiselect_query(custom_key=None):
    def query_helper(key, all_params, schema, context):
        fq = ''
        params = all_params.getall(key)

        # use override key for query if available
        query_key = custom_key if custom_key else key

        def create_single_fq(param, key=query_key):
            return key + ':' + param

        if isinstance(params, basestring): # noqa
            fq = create_single_fq(params)
        elif isinstance(params, list):
            # If all is selected we don't want to return anything
            # because then if an item doesn't have the property it
            # will be filtered out by a query like: key:*
            if 'all' in params:
                return
            fq = ' OR '.join(map(create_single_fq, params))

        return fq
    return query_helper


def advanced_search_and_target_query(keywords_field, target_field):
    def query_helper(key, all_params, schema, context):
        phrase = all_params.getone(keywords_field)
        target = all_params.getone(target_field)

        # Exit early
        if not phrase:
            return '*:*'

        # phrase = hello there
        # query = target:*hello*there*
        schema_target = target
        if target == 'all':
            q = '*' + '*'.join(phrase.split()) + '*'
        else:
            q = schema_target + ':*' + '*'.join(phrase.split()) + '*'

        return q
    return query_helper


def advanced_daterange_query(custom_key=None):
    def query_helper(key, all_params, schema, context):
        before = ''
        after = ''

        if key + '-before' in all_params:
            before = all_params.getone(key + '-before')
        if key + '-after' in all_params:
            after = all_params.getone(key + '-after')

        if not before and not after:
            return

        query_key = custom_key if custom_key else key

        date_to = before + 'T00:00:00Z' if before else '*'
        date_from = after + 'T00:00:00Z' if after else '*'
        q = query_key + ':[' + date_from + ' TO ' + date_to + ']'

        return q
    return query_helper
