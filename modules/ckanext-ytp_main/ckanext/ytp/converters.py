import json
import datetime
import urlparse

from ckan.lib.navl.dictization_functions import Invalid, Missing
from ckan.common import _
from ckan.plugins import toolkit
from ckan.logic.validators import tag_length_validator, tag_name_validator
from itertools import count
from ckan.lib.navl.dictization_functions import Invalid


def to_list_json(value, context):
    """ CKAN converter. Convert value to JSON format. String value is converted to single item list before converting """
    if isinstance(value, basestring):
        value = [value]
    return json.dumps([item for item in value if item])


def from_json_list(value, context):
    """ CKAN converted. Convert value from JSON format. String value is returned as single item list. """
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
        if not url.startswith('www.'):
            raise Invalid(_('Incorrect web address format detected. Web address must start with http://, https:// or www.'))


def is_url(value, context):
    """ CKAN validator. Test is given value is valid URL. Accepts also www-prefix as valid URL. """
    if isinstance(value, basestring):
        _check_url(value)
    elif isinstance(value, list):
        for url in value:
            _check_url(url)

    return value


def string_join(key, data, errors, context):
    """ CKAN converter. Converts list of values to comma-separated list. """
    if isinstance(data[key], Missing):
        return
    data[key] = ",".join(data[key])


def _create_tag(value, context):
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


def _create_vocabulary(id_string):
    """ Create vocabulary. """
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        toolkit.get_action('vocabulary_show')(context, {'id': id_string})
    except toolkit.ObjectNotFound:
        toolkit.get_action('vocabulary_create')(context, {'name': id_string})


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
            _create_vocabulary(vocab)
            v = model.Vocabulary.get(vocab)

        context['vocabulary'] = v

        for num, tag in zip(count(current_index + 1), tags):
            data[('tags', num, 'name')] = tag
            data[('tags', num, 'vocabulary_id')] = v.id

        for tag in tags:
            tag_length_validator(tag, context)
            tag_name_validator(tag, context)
            _create_tag(tag, context)

    return callable_method


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


def simple_date_validate(value, context):
    if value == '' or value is None:
        return ''
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise Invalid(_('Date format incorrect'))
