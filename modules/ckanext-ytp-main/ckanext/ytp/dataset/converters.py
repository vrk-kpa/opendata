from ckan.plugins import toolkit
from ckan.lib.navl.dictization_functions import Invalid, Missing
import datetime
from ckan.common import _
from ckan.logic.validators import tag_length_validator, tag_name_validator
from itertools import count


def _multiple_translations_error():
    raise Invalid(_('Multiple translation in same language'))


def _is_empty(values):
    for value in values:
        if value:
            return False
    return True


def _single_value(values):
    result = None
    for value in values:
        if value:
            if result:
                return None
            else:
                result = value
    return result


def create_vocabulary(id_string):
    """ Create vocabulary. """
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        toolkit.get_action('vocabulary_show')(context, {'id': id_string})
    except toolkit.ObjectNotFound:
        toolkit.get_action('vocabulary_create')(context, {'name': id_string})


def date_validator(value, context):
    """ Validator for date fields """
    if isinstance(value, datetime.date):
        return value
    if value == '':
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise Invalid(_('Date format incorrect'))


def string_join(key, data, errors, context):
    if isinstance(data[key], Missing):
        return
    data[key] = ",".join(data[key])


def create_tag(value, context):
    """ Create tag (value) to vocabulary (context['vocabulary']) """
    model = context['model']
    session = context['session']
    vocabulary = context.get('vocabulary')
    if vocabulary:
        query = session.query(model.Tag)\
            .filter(model.Tag.vocabulary_id == vocabulary.id)\
            .filter(model.Tag.name == value)\
            .count()
        if not query:
            tag = model.Tag(name=value, vocabulary_id=vocabulary.id)
            model.Session.add(tag)
            model.Session.commit()

    return value


def convert_to_tags_string(vocab):
    """ This is modification from CKAN functions convert_to_tags and tag_string_convert.
        Parses tag string and add tags to given vocabulrary.
    """
    def callable_method(key, data, errors, context):
        if isinstance(data[key], basestring):
            tags = [tag.strip() for tag in data[key].split(',') if tag.strip()]
        else:
            tags = data[key]

        current_index = max([int(k[1]) for k in data.keys() if len(k) == 3 and k[0] == 'tags'] + [-1])

        model = context['model']
        v = model.Vocabulary.get(vocab)

        if not v:
            create_vocabulary(vocab)
            v = model.Vocabulary.get(vocab)

        context['vocabulary'] = v

        for num, tag in zip(count(current_index + 1), tags):
            data[('tags', num, 'name')] = tag
            data[('tags', num, 'vocabulary_id')] = v.id

        for tag in tags:
            tag_length_validator(tag, context)
            tag_name_validator(tag, context)
            create_tag(tag, context)

    return callable_method
