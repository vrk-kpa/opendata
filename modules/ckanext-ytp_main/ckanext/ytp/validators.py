import datetime
import iso8601
import pytz

import six
from ckan.common import _
import ckan.authz as authz
import ckan.plugins.toolkit as toolkit
import ckan.model as model
import ckan.logic.validators as validators
import ckan.lib.navl.dictization_functions as df
from ckan.logic import get_action
from ckanext.showcase.model import ShowcaseAdmin

import json
import plugin
import logging
import collections
from tools import check_package_deprecation


try:
    from ckanext.scheming.validation import (
        scheming_validator, validators_from_string)
except ImportError:
    # If scheming can't be imported, return a normal validator instead
    # of the scheming validator
    def scheming_validator(fn):
        def noop(key, data, errors, context):
            return fn(None, None)(key, data, errors, context)
        return noop
    validators_from_string = None

from ckan.common import config
Invalid = df.Invalid
StopOnError = df.StopOnError
missing = df.missing

log = logging.getLogger(__name__)

ObjectNotFound = toolkit.ObjectNotFound
c = toolkit.c

missing = toolkit.missing
ISO_639_LANGUAGE = u'^[a-z][a-z][a-z]?[a-z]?$'


def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s


def list_to_string(list):
    if isinstance(list, collections.Sequence) and not isinstance(list, basestring):
        return ','.join(list)
    return list


def string_to_list(value):
    if isinstance(value, basestring):
        tags = [tag.strip()
                for tag in value.split(',')
                if tag.strip()]
    else:
        tags = value

    return tags


def tag_string_or_tags_required(key, data, errors, context):
    value = data.get(key)
    if not value or value is df.missing:
        data.pop(key, None)
        # Check existence of tags
        if any(k[0] == 'tags' for k in data):
            raise df.StopOnError
        else:
            errors[key].append((_('Missing value')))
            raise df.StopOnError


def set_private_if_not_admin_or_showcase_admin(private):
    userobj = model.User.get(c.user)
    if userobj and not (authz.is_sysadmin(c.user) or ShowcaseAdmin.is_user_showcase_admin(userobj)):
        return True
    else:
        return private


def convert_to_list(value):
    if isinstance(value, basestring):
        tags = [tag.strip()
                for tag in value.split(',')
                if tag.strip()]
    else:
        tags = value

    return tags


def lowercase(value):
    if isinstance(value, six.string_types):
        return value.lower()

    if isinstance(value, list):
        return [v.lower() for v in value]


def create_tags(vocab):
    def callable(key, data, errors, context):

        value = data[key]

        if isinstance(value, list):
            add_to_vocab(context, value, vocab)
            data[key] = json.dumps(value)

    return callable


def create_fluent_tags(vocab):
    def callable(key, data, errors, context):
        value = data[key]
        if isinstance(value, str):
            value = json.loads(value)
        if isinstance(value, dict):
            for lang in value:
                add_to_vocab(context, value[lang], vocab + '_' + lang)
            data[key] = json.dumps(value)

    return callable


def add_to_vocab(context, tags, vocab):

    defer = context.get('defer', False)
    try:
        v = get_action('vocabulary_show')(context, {'id': vocab})
    except ObjectNotFound:
        log.info("creating vocab")
        v = plugin.create_vocabulary(vocab, defer)

    context['vocabulary'] = model.Vocabulary.get(v.get('id'))
    if isinstance(tags, basestring):
        tags = [tags]

    for tag in tags:
        validators.tag_length_validator(tag, context)
        validators.tag_name_validator(tag, context)

        try:
            validators.tag_in_vocabulary_validator(tag, context)
        except Invalid:
            plugin.create_tag_to_vocabulary(tag, vocab, defer)


def tag_list_output(value):
    if isinstance(value, dict) or len(value) == 0:
        return value
    return json.loads(value)


def repeating_text(key, data, errors, context):
    """
    Accept repeating text input in the following forms
    and convert to a json list for storage:

    1. a list of strings, eg.

       ["Person One", "Person Two"]

    2. a single string value to allow single text fields to be
       migrated to repeating text

       "Person One"

    3. separate fields per language (for form submissions):

       fieldname-0 = "Person One"
       fieldname-1 = "Person Two"
    """
    # just in case there was an error before our validator,
    # bail out here because our errors won't be useful
    if errors[key]:
        return

    value = data[key]
    # 1. list of strings or 2. single string
    if value is not toolkit.missing:
        if isinstance(value, basestring):
            value = [value]
        if not isinstance(value, list):
            errors[key].append(_('expecting list of strings'))
            return

        out = []
        for element in value:
            if not isinstance(element, basestring):
                errors[key].append(_('invalid type for repeating text: %r')
                                   % element)
                continue
            if isinstance(element, str):
                try:
                    element = element.decode('utf-8')
                except UnicodeDecodeError:
                    errors[key]. append(_('invalid encoding for "%s" value')
                                        % toolkit.lang)
                    continue
            out.append(element)

        if not errors[key]:
            data[key] = json.dumps(out)
        return

    # 3. separate fields
    found = {}
    prefix = key[-1] + '-'
    extras = data.get(key[:-1] + ('__extras',), {})

    for name, text in extras.iteritems():
        if not name.startswith(prefix):
            continue
        if not text:
            continue
        index = name.split('-', 1)[1]
        try:
            index = int(index)
        except ValueError:
            continue
        found[index] = text

    out = [found[i] for i in sorted(found)]
    data[key] = json.dumps(out)


def repeating_text_output(value):
    """
    Return stored json representation as a list, if
    value is already a list just pass it through.
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    try:
        return json.loads(value)
    except ValueError:
        return [value]


def repeating_email(key, data, errors, context):
    if errors[key]:
        return

    value_json = data[key]
    value = json.loads(value_json)

    if not isinstance(value, list):
        errors[key].append(_('expecting a list'))
        return

    email_validator = toolkit.get_validator('email_validator')
    for item in value:
        email_validator(item, context)


@scheming_validator
def only_default_lang_required(field, schema):
    default_lang = ''
    if field and field.get('only_default_lang_required'):
        default_lang = config.get('ckan.locale_default', 'en')

    def validator(key, data, errors, context):
        if errors[key]:
            return

        value = data[key]

        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except ValueError:
                    errors[key].append(_('Failed to decode JSON string'))
                    return
                except UnicodeDecodeError:
                    errors[key].append(_('Invalid encoding for JSON string'))
                    return
            if not isinstance(value, dict):
                errors[key].append(_('expecting JSON object'))
                return

            if field.get('only_default_lang_required') is True and value.get(default_lang, '') == '':
                errors[key].append(_('Required language "%s" missing') % default_lang)
            return

        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        if extras.get(prefix + default_lang, '') == '':
            errors[key].append(_('Required language "%s" missing') % default_lang)

    return validator


def override_field(overridden_field_name):
    @scheming_validator
    def implementation(field, schema):

        from ckan.lib.navl.dictization_functions import missing

        def validator(key, data, errors, context):
            override_value = data[key]
            if override_value not in (None, missing):
                overridden_key = tuple(overridden_field_name.split('.'))
                data[overridden_key] = override_value

        return validator

    return implementation


def override_field_with_default_translation(overridden_field_name):
    @scheming_validator
    def implementation(field, schema):

        from ckan.lib.navl.dictization_functions import missing

        default_lang = config.get('ckan.locale_default', 'en')

        def validator(key, data, errors, context):
            value = data[key]
            override_value = missing

            if value is not missing:
                if isinstance(value, basestring):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        errors[key].append(_('Failed to decode JSON string'))
                        return
                    except UnicodeDecodeError:
                        errors[key].append(_('Invalid encoding for JSON string'))
                        return
                if not isinstance(value, dict):
                    errors[key].append(_('expecting JSON object'))
                    return

                override_value = value.get(default_lang, missing)

            if override_value not in (None, missing):
                overridden_key = tuple(overridden_field_name.split('.'))
                data[overridden_key] = override_value

        return validator

    return implementation


@scheming_validator
def keep_old_value_if_missing(field, schema):
    from ckan.lib.navl.dictization_functions import missing, flatten_dict
    from ckan.logic import get_action

    def validator(key, data, errors, context):

        if 'package' not in context:
            return

        data_dict = flatten_dict(get_action('package_show')(context, {'id': context['package'].id}))

        if key not in data or data[key] is missing:
            if key in data_dict:
                data[key] = data_dict[key]

    return validator


def ignore_if_invalid_isodatetime(v):
    try:
        iso8601.parse_date(v)
        return v
    except iso8601.ParseError:
        return None


@scheming_validator
def from_date_is_before_until_date(field, schema):

    max_date_field = None
    min_date_field = None
    if field and field.get('max_date_field'):
        max_date_field = (field.get('max_date_field'),)

    if field and field.get('min_date_field'):
        min_date_field = (field.get('min_date_field'),)

    def validator(key, data, errors, context):

        max_date_value = data.get(max_date_field, "")
        if max_date_field is not None and max_date_value != "" and max_date_value != missing:
            if not isinstance(max_date_value, datetime.datetime):
                try:
                    max_date_value = iso8601.parse_date(max_date_value)
                except iso8601.ParseError:
                    log.info("Could not convert %s to datetime" % max_date_value)
                    pass
            if data[key] and data[key].replace(tzinfo=pytz.utc) > max_date_value:
                errors[key].append(_('Start date is after end date'))

        min_date_value = data.get(min_date_field, "")
        if min_date_field is not None and min_date_value != "" and min_date_value != missing:
            if not isinstance(min_date_value, datetime.datetime):
                try:
                    min_date_value = iso8601.parse_date(min_date_value)
                except iso8601.ParseError:
                    log.info("Could not convert %s to datetime" % min_date_value)
                    pass
            if data[key] and data[key].replace(tzinfo=pytz.utc) < min_date_value:
                errors[key].append(_('End date is before start date'))

    return validator


@scheming_validator
def is_admin_in_parent_if_changed(field, schema):

    def validator(key, data, errors, context):

        if context.get('group') is not None:
            old_organization = get_action('organization_show')(context, {'id': context['group'].id,
                                                                         'include_users': False,
                                                                         'include_dataset_count': False,
                                                                         'include_groups': False,
                                                                         'include_tags': False,
                                                                         'include_followers': False})
            old_parent_group_names = [org['name'] for org in old_organization.get('groups', [])]
        else:
            old_parent_group_names = []

        user = context['user']

        # Uses CKAN core function to specify parent, in html groups__0__name
        actual_key = ("groups", 0, "name")

        if data.get(actual_key):

            if not authz.is_sysadmin(user):

                selected_organization = get_action('organization_show')(context, {'id': data[actual_key],
                                                                                  'include_users': False,
                                                                                  'include_dataset_count': False,
                                                                                  'include_groups': False,
                                                                                  'include_tags': False,
                                                                                  'include_followers': False})

                if data[actual_key] and data[actual_key] not in old_parent_group_names:
                    admin_in_orgs = model.Session.query(model.Member).filter(model.Member.state == 'active')\
                        .filter(model.Member.table_name == 'user')\
                        .filter(model.Member.capacity == 'admin')\
                        .filter(model.Member.table_id == authz.get_user_id_for_username(user, allow_none=True))

                    if not any(selected_organization['name'] == admin_org.group.name for admin_org in admin_in_orgs):
                        errors[key].append(_('User %s is not administrator in the selected parent organization') % user)

        # Remove parent_org from data as it is missing from the form
        data.pop(key, None)

        # Stop validation if error has happened
        raise StopOnError

    return validator


@scheming_validator
def extra_validators_multiple_choice(field, schema):
    static_extra_validators = None
    if 'choices' in field:
        static_extra_validators = [{"value": c['value'], 'validator': c.get('extra_validator')}
                                   for c in field['choices'] if c.get('extra_validator')]

    def validator(key, data, errors, context):

        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        if context.get('group'):
            old_organization = get_action('organization_show')(context, {'id': context['group'].id,
                                                                         'include_users': False,
                                                                         'include_dataset_count': False,
                                                                         'include_groups': False,
                                                                         'include_tags': False,
                                                                         'include_followers': False})
            old_features = old_organization.get('features', [])
        else:
            old_features = []

        value = json.loads(data[key])
        extra_validators = static_extra_validators

        changed_features = list(set(old_features).symmetric_difference(value))

        for extra_validator in extra_validators:
            if extra_validator.get('value') in changed_features:
                context['field'] = extra_validator.get('value')
                toolkit.get_validator(extra_validator.get('validator'))(key, data, errors, context)

    return validator


def admin_only_feature(key, data, errors, context):
    if not authz.is_sysadmin(context['user']):
        errors[key].append(_('Only sysadmin can change feature: %s') % context['field'])


def check_deprecation(key, data, errors, context):
    # just in case there was an error before our validator,
    # bail out here because our errors won't be useful
    if errors[key]:
        return

    deprecation = check_package_deprecation(data.get(('valid_till',)))
    data[key] = deprecation


@scheming_validator
def admin_only_field(field, schema):
    from ckan.lib.navl.dictization_functions import flatten_dict
    from ckan.logic import get_action

    def validator(key, data, errors, context):

        if 'package' not in context:
            return

        data_dict = flatten_dict(get_action('package_show')(context, {'id': context['package'].id}))

        if not authz.is_authorized('sysadmin', context).get('success'):
            if key in data_dict:
                data[key] = data_dict[key]
            else:
                del data[key]

    return validator


@scheming_validator
def use_url_for_name_if_left_empty(field, schema):
    def validator(key, data, errors, context):
        resource_names_translated = json.loads(data.get(key, ''))
        resource_url = data.get(key[:-1] + ('url',), '')

        if resource_names_translated.get('fi', '') == '' and resource_url != '':
            resource_names_translated['fi'] = resource_url
            data[key] = json.dumps(resource_names_translated)
    return validator


def convert_to_json_compatible_str_if_str(value):
    if isinstance(value, basestring):
        if value == "":
            return json.dumps({})
        try:
            json.loads(value)
        except ValueError:
            value = json.dumps({'fi': value})
        return value


def empty_string_if_value_missing(key, data, errors, context):
    value = data.get(key)
    if not value or value is missing:
        data[key] = ''


def repeating_url(key, data, errors, context):
    if errors[key]:
        return

    value_json = data[key]
    value = json.loads(value_json)

    if not isinstance(value, list):
        errors[key].append(_('expecting a list'))
        return

    url_validator = toolkit.get_validator('url_validator')
    for item in value:
        url_validator(key, {key: item}, errors, context)


def resource_url_validator(key, data, errors, context):
    if errors[key]:
        return

    url_type = data[(key[0], key[1], 'url_type')]
    if url_type != u'upload':
        url_validator = toolkit.get_validator('url_validator')
        url_validator(key, data, errors, context)
