from ckan.lib import helpers
import json
import urllib2
from pylons import config


def _markdown(translation, length):
    return helpers.markdown_extract(translation, extract_length=length) if length is not True and isinstance(length, (int, long)) else \
        helpers.render_markdown(translation)


def extra_translation(values, field, markdown=False, fallback=None):
    """ Used as helper. Get correct translation from extras (values) for given field.
        If markdown is True uses markdown rendering for value. If markdown is number use markdown_extract with given value.
        If fallback is set then use fallback as value if value is empty.
        If fallback is function then call given function with `values`.
    """
    lang = ""
    try:
        lang = helpers.lang()
    except TypeError:
        pass

    translation = values.get('%s_%s' % (field, lang), "") or values.get(field, "") if values else ""

    if not translation and fallback:
        translation = fallback(values) if hasattr(fallback, '__call__') else fallback

    return _markdown(translation, markdown) if markdown and translation else translation


def get_dict_tree_from_json(fileurl_variable_name):
    """ Parse a JSON file and return it for constructing UI trees. """

    file_url = config.get(fileurl_variable_name, None)
    if file_url:
        return json.load(urllib2.urlopen(file_url))
    else:
        return []
