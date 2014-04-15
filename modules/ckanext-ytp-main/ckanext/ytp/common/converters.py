import json
from ckan.lib.navl.dictization_functions import Invalid
import urlparse
from ckan.common import _


def to_list_json(value, context):
    if isinstance(value, basestring):
        value = [value]
    return json.dumps([item for item in value if item])


def from_json_list(value, context):
    if not value:
        return value
    try:
        if isinstance(value, basestring):
            parsed_value = json.loads(value)
            if not isinstance(parsed_value, list):
                return [value]
            return parsed_value
    except:
        pass
    return [unicode(value)]  # Return original string as list for non converted values


def _check_url(url):
    if not url:
        return
    parts = urlparse.urlsplit(url)
    if not parts.scheme or not parts.netloc:
        raise Invalid(_('Incorrect URL format'))


def is_url(value, context):
    if isinstance(value, basestring):
        _check_url(value)
    elif isinstance(value, list):
        for url in value:
            _check_url(url)

    return value
