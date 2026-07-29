from flask_babel import force_locale
from ckan.lib.mailer import mail_user, mail_recipient
from ckan.common import _
from ckan.plugins import toolkit
import logging

log = logging.getLogger(__name__)


def _SUBJECT_MEMBERSHIP_REQUEST():
    return _(
        "New membership request (%(organization)s)")


def _MESSAGE_MEMBERSHIP_REQUEST():
    return _("""\
User %(user)s (%(email)s) has requested membership to organization %(organization)s.

%(link)s

Best regards

Suomi.fi Open Data support
avoindata@dvv.fi
""")


def _SUBJECT_MEMBERSHIP_APPROVED():
    return _(
        "Organization membership approved (%(organization)s)")


def _MESSAGE_MEMBERSHIP_APPROVED():
    return _("""\
Your membership request to organization %(organization)s with %(role)s access has been approved.

Best regards

Suomi.fi Open Data support
avoindata@dvv.fi
""")


def _SUBJECT_MEMBERSHIP_REJECTED():
    return _(
        "Organization membership rejected (%(organization)s)")


def _MESSAGE_MEMBERSHIP_REJECTED():
    return _("""\
Your membership request to organization %(organization)s with %(role)s access has been rejected.

Best regards

Suomi.fi Open Data support
avoindata@dvv.fi
""")


def mail_new_membership_request(locale, admin, group_name, url, user_name, user_email):
    # TODO: Set admin locale. Admin/user locale is stored at drupal database so may be a bit challenging to fetch it.
    # We default to finnish for the time being

    with force_locale('fi'):
        subject = _SUBJECT_MEMBERSHIP_REQUEST() % {
            'organization': group_name
        }
        message = _MESSAGE_MEMBERSHIP_REQUEST() % {
            'user': user_name,
            'email': user_email,
            'organization': group_name,
            'link': url
        }

    try:
        mail_user(admin, subject, message)
    except Exception:
        log.exception("Mail could not be sent")


def mail_process_status(locale, member_user, approve, group_name, capacity):
    with force_locale(locale):
        role_name = _(capacity)

        subject_template = _SUBJECT_MEMBERSHIP_APPROVED(
        ) if approve else _SUBJECT_MEMBERSHIP_REJECTED()
        message_template = _MESSAGE_MEMBERSHIP_APPROVED(
        ) if approve else _MESSAGE_MEMBERSHIP_REJECTED()

    subject = subject_template % {
        'organization': group_name
    }
    message = message_template % {
        'role': role_name,
        'organization': group_name
    }

    try:
        mail_user(member_user, subject, message)
    except Exception:
        log.exception("Mail could not be sent")
        # raise MailerException("Mail could not be sent")

    admin_email = toolkit.config.get('ckanext.ytp_request.admin_email')
    if admin_email:
        try:
            mail_recipient('Admin notifications', admin_email,
                           f'(sent to {member_user.name}) {subject}', message)
        except Exception:
            log.exception("Mail could not be sent")
