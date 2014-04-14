import json


def to_list_json(value, context):
    if isinstance(value, basestring):
        value = [value]
    return json.dumps([item for item in value if item])


def from_json_list(value, context):
    try:
        parsed_value = json.loads(value)
        if not isinstance(parsed_value, list):
            return [value]
        return parsed_value
    except Exception, e:
        if isinstance(value, basestring):
            return [value]  # Return original string as list for non converted values
        raise e
