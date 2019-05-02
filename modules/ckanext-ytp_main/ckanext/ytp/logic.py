from ckan import logic
from ckan.common import _, c
from ckan.logic import auth
from ckan.model import Package
from ckan.lib.mailer import mail_recipient

import logging
import sqlalchemy
import sqlalchemy.sql

_select = sqlalchemy.sql.select
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case

log = logging.getLogger(__name__)


# Insert here the fields that are localized
_localized_fields = ['job_title', 'about']


@logic.auth_allow_anonymous_access
def auth_user_update(context, data_dict):
    """ Modified from CKAN: user_update """
    user = context['user']

    # FIXME: We shouldn't have to do a try ... except here, validation should
    # have ensured that the data_dict contains a valid user id before we get to
    # authorization.
    try:
        user_obj = auth.get_user_object(context, data_dict)
    except logic.NotFound:
        return {'success': False, 'msg': _('User not found')}

    if 'name' in data_dict and data_dict['name'] != user:
        return {'success': False, 'msg': _('Cannot change username')}
    if 'email' in data_dict and data_dict['email'] != user_obj.email:
        return {'success': False, 'msg': _('Cannot change email')}

    # If the user has a valid reset_key in the db, and that same reset key
    # has been posted in the data_dict, we allow the user to update
    # her account without using her password or API key.
    if user_obj.reset_key and 'reset_key' in data_dict:
        if user_obj.reset_key == data_dict['reset_key']:
            return {'success': True}

    if not user:
        return {'success': False,
                'msg': _('Have to be logged in to edit user')}

    if user == user_obj.name:
        # Allow users to update their own user accounts.
        return {'success': True}
    else:
        # Don't allow users to update other users' accounts.
        return {'success': False,
                'msg': _('User %s not authorized to edit user %s') %
                        (user, user_obj.id)}


def auth_user_list(context, data_dict):
    if not c.user:
        return {'success': False, 'msg': _('Have to be logged in to list users')}
    return {'success': True}


def auth_admin_list(context, data_dict):
    if not c.user:
        return {'success': False, 'msg': _('Have to be logged in to list admins')}
    return {'success': True}


def send_package_deprecation_emails(packages):
    grouped_by_maintainer = {}
    for package in packages:
        fullPackage = Package.get(package)
        maintainer_email = fullPackage.maintainer_email

        packageInfoForEmail = {
            "title": fullPackage.title,
            "id": fullPackage.id,
            "valid_till": fullPackage.extras.get("valid_till"),
        }

        if maintainer_email not in grouped_by_maintainer:
            grouped_by_maintainer[maintainer_email] = {"maintainer": fullPackage.maintainer, "packages": [packageInfoForEmail]}
        else:
            grouped_by_maintainer[maintainer_email]["packages"].append(packageInfoForEmail)

    for maintainer_email, details in grouped_by_maintainer.iteritems():
        send_deprecation_email_user(
            maintainer_email,
            details["packages"],
            details["maintainer"],
            details["packages"][0]["valid_till"]
        )


def send_deprecation_email_user(maintainer_email, packages, maintainer, valid_till):
    from email_templates import deprecation_email_user
    log.info('send deprecation email user')
    subject = deprecation_email_user.subject.format(valid_till=valid_till)
    body = deprecation_email_user.messageBody(maintainer, packages)
    mail_recipient(maintainer, maintainer_email, subject, body)
