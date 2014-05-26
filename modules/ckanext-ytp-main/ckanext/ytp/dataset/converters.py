from ckan.lib.navl.dictization_functions import Invalid
import datetime
from ckan.common import _


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
    if value == '' or value == None :
        return ''
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise Invalid(_('Date format incorrect'))
