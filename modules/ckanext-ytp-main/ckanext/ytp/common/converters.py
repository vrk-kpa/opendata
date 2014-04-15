import json


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
