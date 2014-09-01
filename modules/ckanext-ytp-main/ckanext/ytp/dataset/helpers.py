from pylons import config
import json

from ckan.common import c, request


def service_database_enabled():
    return config.get('ckanext.ytp.dataset.service_database_enabled', 'true') == 'true'


def get_json_value(value):
    try:
        return json.loads(value)
    except:
        return value


def sort_datasets_by_state_priority(datasets):
    """ Sorts the given list of datasets so that drafts appear first and deleted ones last. Also secondary sorts by modification date, latest first. """

    sorted_datasets = []
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] == 'draft'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] not in ['draft', 'deleted']],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] == 'deleted'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    return sorted_datasets


def get_remaining_facet_item_count(facet, limit=10):
    items = c.search_facets.get(facet)['items']
    return len(items) - 1 - limit


def sort_facet_items_by_name(items):
    sorted_items = []
    sorted_items.extend(sorted([item for item in items if item['active'] is True], key=lambda item: (-item['count'], item['display_name'])))
    sorted_items.extend(sorted([item for item in items if item['active'] is False], key=lambda item: (-item['count'], item['display_name'])))
    return sorted_items


def get_sorted_facet_items_dict(facet, limit=10, exclude_active=False):
    if not c.search_facets or \
            not c.search_facets.get(facet) or \
            not c.search_facets.get(facet).get('items'):
        return []
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        if not len(facet_item['name'].strip()):
            continue
        if not (facet, facet_item['name']) in request.params.items():
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            facets.append(dict(active=True, **facet_item))
    sorted_items = []
    sorted_items.extend(sorted([item for item in facets if item['active'] is True], key=lambda item: item['display_name'].lower()))
    sorted_items.extend(sorted([item for item in facets if item['active'] is False], key=lambda item: item['display_name'].lower()))

    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return sorted_items[:limit]
    else:
        return sorted_items
