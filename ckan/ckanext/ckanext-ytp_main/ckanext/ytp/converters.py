import json
import datetime
import urllib.parse
import logging
from ckan.lib.navl.dictization_functions import Invalid, Missing, missing, flatten_list, StopOnError
from ckan.common import _
from ckan.plugins import toolkit
from ckan.logic.validators import tag_length_validator, tag_name_validator
from itertools import count

log = logging.getLogger(__name__)


def to_list_json(value, context):
    """ CKAN converter. Convert value to JSON format. String value is converted to single item list before converting """
    if isinstance(value, str):
        value = [value]
    return json.dumps([item for item in value if item])


def from_json_list(value, context):
    """ CKAN converted. Convert value from JSON format. String value is returned as single item list. """
    if not value:
        return value
    try:
        if isinstance(value, str):
            parsed_value = json.loads(value)
            if not isinstance(parsed_value, list):
                return [value]
            return parsed_value
    except Exception as e:
        print(e)
        pass
    return [str(value)]  # Return original string as list for non converted values


def _check_url(url):
    if not url:
        return
    parts = urllib.parse.urlsplit(url)
    if not parts.scheme or not parts.netloc:
        if not url.startswith('www.'):
            raise Invalid(_('Incorrect web address format detected. Web address must start with http://, https:// or www.'))


def is_url(value, context):
    """ CKAN validator. Test is given value is valid URL. Accepts also www-prefix as valid URL. """
    if isinstance(value, str):
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
        if isinstance(data[key], str):
            tags = [tag.strip() for tag in data[key].split(',') if tag.strip()]
        else:
            tags = data[key]

        current_index = max([int(k[1]) for k in list(data.keys()) if len(k) == 3 and k[0] == 'tags'] + [-1])

        model = context['model']
        v = model.Vocabulary.get(vocab)

        if not v:
            _create_vocabulary(vocab)
            v = model.Vocabulary.get(vocab)

        context['vocabulary'] = v

        if len(tags) > 0 and data.get(('tags',)) == []:
            del data[('tags',)]

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


def save_to_groups(key, data, errors, context):
    # https://docs.ckan.org/en/ckan-2.7.3/api/#ckan.logic.action.create.package_create
    # Add selected items as groups to dataset
    value = data[key]

    if value and value is not missing:

        if isinstance(value, str):
            group_patch = flatten_list([{"name": value}])
            group_key = ('groups',) + list(group_patch.keys())[0]
            group_value = list(group_patch.values())[0]
            data[group_key] = group_value
        else:
            if isinstance(value, list):
                data[key] = json.dumps(value)
                groups_with_details = []
                for identifier in value:
                    groups_with_details.append({"name": identifier})
                group_patch = flatten_list(groups_with_details)

                for k, v in list(group_patch.items()):
                    group_key = ('groups',) + k
                    data[group_key] = v

    else:

        # Delete categories key if it is missing
        # TODO: Should delete existing groups from dataset
        data.pop(key, None)
        raise StopOnError

    return data[key]
