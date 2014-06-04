from pylons import config
import json


def service_database_enabled():
    return config.get('ckanext.ytp.dataset.service_database_enabled', 'true') == 'true'


def get_json_value(value):
    try:
        return json.loads(value)
    except:
        return value
