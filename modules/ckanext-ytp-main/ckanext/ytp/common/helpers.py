from ckan.lib import helpers


def _markdown(translation, length):
    return helpers.markdown_extract(translation, extract_length=length) if length is not True and isinstance(length, (int, long)) else \
        helpers.render_markdown(translation)


def extra_translation(values, field, markdown=False, fallback=None):
    """ Used as helper. Get correct translation from extras (values) for given field.
        If markdown is True uses markdown rendering for value. If markdown is number use markdown_extract with given value.
        If fallback is set then use fallback as value if value is empty.
        If fallback is function then call given function with `values`.
    """
    translation = values.get('%s_%s' % (field, helpers.lang()), "") or values.get(field, "") if values else ""

    if not translation and fallback:
        translation = fallback(values) if hasattr(fallback, '__call__') else fallback

    return _markdown(translation, markdown) if markdown and translation else translation


def get_dict_tree_from_json(filename):
    return [{'text': 'root 1', 'children': [{'text': 'child 1', 'children': ['child of child']},
                                            {'text': 'child 2', 'children': [{'text': 'child of child 2', 'children': ['child of child of child']}]}]},
            {'text': 'root 2', 'children': ['child 3 as string']}]
