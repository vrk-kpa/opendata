import iso8601
import six
from ckan import model, plugins
from ckan.plugins import toolkit
from ckanext.ytp.converters import to_list_json, from_json_list
from ckan.lib import helpers
import os
from datetime import datetime
import pytz


def create_system_context():
    """ Helper method to create system context for CKAN actions. """
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
    context['user'] = admin_user['name']
    return context


def get_locales():
    """ Return all available locales strings. """
    return [locale.language for locale in helpers.i18n.get_available_locales()]


def add_translation_modify_schema(schema):
    """Modifies the given schema with translation related keys"""
    ignore_missing = toolkit.get_validator('ignore_missing')
    convert_to_extras = toolkit.get_converter('convert_to_extras')

    schema.update({'original_language': [ignore_missing, str, convert_to_extras]})
    schema.update({'translations': [ignore_missing, to_list_json, convert_to_extras]})
    return schema


def add_languages_modify(schema, fields, locales=None):
    """Adds localized field keys to the given schema"""
    if locales is None:
        locales = get_locales()
    ignore_missing = toolkit.get_validator('ignore_missing')
    convert_to_extras = toolkit.get_converter('convert_to_extras')
    for locale in locales:
        for field in fields:
            schema.update({"%s_%s" % (field, locale): [ignore_missing, str, convert_to_extras]})
    return schema


def add_translation_show_schema(schema):
    """ Add translation definitions into given schema """
    ignore_missing = toolkit.get_validator('ignore_missing')
    convert_from_extras = toolkit.get_converter('convert_from_extras')
    schema.update({'original_language': [convert_from_extras, ignore_missing]})
    schema.update({'translations': [convert_from_extras, from_json_list, ignore_missing]})
    return schema


def add_languages_show(schema, fields, locales=None):
    """ Add translation to schema to given fields. """
    if locales is None:
        locales = get_locales()
    convert_from_extras = toolkit.get_converter('convert_from_extras')
    ignore_missing = toolkit.get_validator('ignore_missing')
    for locale in locales:
        for field in fields:
            schema.update({"%s_%s" % (field, locale): [convert_from_extras, ignore_missing]})
    return schema


def get_organization_test_source():
    return "file://%s" % os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/organization.json')


def get_organization_harvest_test_source():
    return "file://%s" % os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/organization_harvest.json')


# Packages are deprecated if their valid_till date has passed
# By default packages are not deprecated
def check_package_deprecation(valid_till):
    time_now = datetime.now(pytz.utc)

    if isinstance(valid_till, six.text_type):
        try:
            valid_till = iso8601.parse_date(valid_till)
        except iso8601.ParseError:
            return False

    if not valid_till or valid_till == toolkit.missing:
        return False
    elif valid_till < time_now:
        return True
    return False
