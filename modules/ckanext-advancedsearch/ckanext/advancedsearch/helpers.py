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
