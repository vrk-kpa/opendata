from pylons import config
import json


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
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state']=='draft'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] not in ['draft','deleted']],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state']=='deleted'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    return sorted_datasets
