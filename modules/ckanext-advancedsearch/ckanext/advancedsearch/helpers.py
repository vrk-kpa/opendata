from ckan.logic import get_action
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
def category_options(field):
    from ckan import model

    context = {'model': model, 'session': model.Session}
    groups = get_action('group_list')(context, {})

    options = []
    for group in groups:
        group_details = get_action('group_show')(context, {"id": group})
        options.append({"value": group_details['display_name'], "label": group_details['title']})

    return options


def publisher_options(field):
    from ckan import model
    import ckan.plugins as p

    context = {'model': model, 'session': model.Session}
    publishers = p.toolkit.get_action('get_organizations')(context, {})

    return make_options(publishers)


def license_options(field):
    from ckan import model
    context = {'model': model, 'session': model.Session}

    licenses = get_action('license_list')(context)

    return make_options(licenses)


def format_options(field):
    # TODO: define query to fetch format details
    return [
        {"value": "1", "label": "API"},
        {"value": "2", "label": "CSV"},
        {"value": "3", "label": "CSV / ZIP"},
        {"value": "4", "label": "Database"},
        {"value": "5", "label": "DOC"},
        {"value": "6", "label": "ESRI REST"},
        {"value": "7", "label": "GEOJSON"}
    ]


def make_options(items, value='id', label="title"):
    options = []
    for item in items:
        options.append({"value": item[value], "label": item[label]})

    return options