import json
import logging

from ckan import model
from ckan.common import _
from ckan.plugins.toolkit import c, check_access, get_action
# TODO: Should not be cross dependant to ckanext.ytp
# This is specific to ytp
from ckanext.ytp.helpers import get_translated

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


# twig helper to get the value based on a dynamic key
def value_or_blank(item, key):
    if item:
        return item[key] if key in item else ''
    return ''


# finds the index of previously selected radio
# twig loop indexes start from 1
def selected_indexes_checkboxes(options, prev_selected):
    indexes = []
    loop_index = 1
    all_selected = True
    for option in options:
        if option['value'] in prev_selected:
            indexes.append(loop_index)
        else:
            all_selected = False
        loop_index = loop_index + 1
    return {'indexes': indexes, 'all_selected': all_selected}


def selected_index_radio(options, prev_selected):
    index = 1
    for option in options:
        if option['value'] == prev_selected:
            return index
        index = index + 1
    return 1


def query_helper(field):
    """
    :param field: scheming field definition
    :returns: query helper function result or None if not found.
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
    context = {'model': model, 'session': model.Session}
    groups = get_action('group_list')(context, {"all_fields": True, "include_extras": True})

    return make_options(groups, value="name", has_translated=True)


def advanced_publisher_options(field=None):
    check_access('organization_list', {'user': c.user, 'model': model, 'session': model.Session})
    data = model.Session.query(model.Group.name, model.Group.title, model.GroupExtra.value) \
        .join(model.GroupExtra, model.GroupExtra.group_id == model.Group.id) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .filter(model.GroupExtra.state == u'active')\
        .filter(model.GroupExtra.key == u'title_translated')\
        .all()

    publishers = [
            {'id': gid, 'title': title, 'title_translated': json.loads(title_translated)}
            for gid, title, title_translated in data]
    return make_options(publishers, has_translated=True)


def advanced_license_options(field=None):
    context = {'model': model, 'session': model.Session}

    licenses = get_action('license_list')(context)

    return make_options(licenses)


def advanced_dataset_types_options(field=None):
    dataset_types = [{"value": "dataset", "label": _("Datasets")}, {"value": "showcase", "label": _("Showcases")}]

    return make_options(dataset_types, value="value", label="label")


def advanced_format_options(field=None):
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
        params = all_params.getlist(key)

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
        phrase = None
        target = 'all'
        if keywords_field in all_params:
            phrase = all_params.get(keywords_field)
        if target_field in all_params:
            target = all_params.get(target_field)

        # Exit early
        if not phrase:
            return '*:*'

        # phrase = hello there
        # query = target:*hello*there*
        if target == 'all':
            q = '*' + '*'.join(phrase.split()) + '*'
        else:
            q = target + ':*' + '*'.join(phrase.split()) + '*'

        return q
    return query_helper


def advanced_search_query(keywords_field):
    def query_helper(key, all_params, schema, context):
        phrase = None
        if keywords_field in all_params:
            phrase = all_params.get(keywords_field)

        # Exit early
        if not phrase:
            return '*:*'

        return phrase
    return query_helper


def advanced_daterange_query(custom_key=None):
    def query_helper(key, all_params, schema, context):
        before = ''
        after = ''

        if key + '-before' in all_params:
            before = all_params.get(key + '-before')
        if key + '-after' in all_params:
            after = all_params.get(key + '-after')

        # exit early
        if not before and not after:
            return

        query_key = custom_key if custom_key else key

        date_to = before + 'T00:00:00Z' if before else '*'
        date_from = after + 'T00:00:00Z' if after else '*'
        q = query_key + ':[' + date_from + ' TO ' + date_to + ']'

        return q
    return query_helper
