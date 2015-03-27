from pylons import config
import json
from ckan.common import c, request
from ckan.logic import get_action


def service_database_enabled():
    return config.get('ckanext.ytp.dataset.service_database_enabled', 'true') == 'true'


def get_json_value(value):
    """ Get value as JSON. If value is not in JSON format return the given value """
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


def calculate_datasets_five_star_rating(dataset_id):
    from ckanext.qa.reports import five_stars

    qa = five_stars(dataset_id)

    stars = 0
    for resource in qa:
        if resource['openness_score'] > stars:
            stars = resource['openness_score']

    return int(stars)


def get_upload_size():
    size = config.get('ckan.max_resource_size', 10)

    return size


def get_license(license_id):
    context = {}
    licenses = get_action('license_list')(context, {})

    for license_obj in licenses:
        license_obj_id = license_obj.get('id', None)
        print license_obj
        if license_obj_id and license_obj_id == license_id:
            return license_obj

    return None
