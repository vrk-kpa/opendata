from ckan.lib.navl.dictization_functions import Invalid
import datetime
from ckan.common import _


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
