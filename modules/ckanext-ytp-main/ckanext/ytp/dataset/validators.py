from ckan.common import _
import ckan.authz as authz
import ckan.plugins.toolkit as toolkit
import collections

import ckan.model as model
import ckan.logic.validators as validators
import ckan.lib.navl.dictization_functions as df
import re
import json
from ckan.logic import get_action


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

import plugin

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


def set_private_if_not_admin(private):
    return True if not authz.is_sysadmin(c.user) else private

def convert_to_list(value):
    if isinstance(value, basestring):
        tags = [tag.strip().lower() \
                for tag in value.split(',') \
                if tag.strip()]
    else:
        tags = value

    return tags



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
    try:
        v = get_action('vocabulary_show')(context, {'id': vocab})
    except ObjectNotFound:
        v = plugin.create_vocabulary(vocab)


    if isinstance(tags, basestring):
        tags = [tags]

    for tag in tags:
        validators.tag_length_validator(tag, context)
        validators.tag_name_validator(tag, context)

        try:
            validators.tag_in_vocabulary_validator(tag, context)
        except Invalid:
            plugin.create_tag_to_vocabulary(tag, vocab)


def tag_list_output(value):
    if isinstance(value, dict) or len(value) is 0:
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


@scheming_validator
def only_default_lang_required(field, schema):
    default_lang = ''
    if field and field.get('only_default_lang_required'):
        default_lang =  config.get('ckan.locale_default', 'en')

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

            if field.get('only_default_lang_required') is not None and value.get(default_lang) is None:
                errors[key].append(_('Required language "%s" missing') % default_lang)
            return

        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        if extras.get(prefix + default_lang) == '' or extras.get(prefix + default_lang) is None:
            errors[key].append(_('Required language "%s" missing') % default_lang)

    return  validator
