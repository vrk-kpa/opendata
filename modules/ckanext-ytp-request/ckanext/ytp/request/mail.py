from ckan.lib.i18n import set_lang, get_lang
from ckan.lib.mailer import mail_user
from pylons import i18n
from ckan.common import _
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

Avoindata.fi support
avoindata@vrk.fi
""")


def _SUBJECT_MEMBERSHIP_APPROVED():
    return _(
            "Organization membership approved (%(organization)s)")


def _MESSAGE_MEMBERSHIP_APPROVED():
    return _("""\
Your membership request to organization %(organization)s with %(role)s access has been approved.

Best regards

Avoindata.fi support
avoindata@vrk.fi
""")


def _SUBJECT_MEMBERSHIP_REJECTED():
    return _(
            "Organization membership rejected (%(organization)s)")


def _MESSAGE_MEMBERSHIP_REJECTED():
    return _("""\
Your membership request to organization %(organization)s with %(role)s access has been rejected.

Best regards

Avoindata.fi support
avoindata@vrk.fi
""")


def mail_new_membership_request(locale, admin, group_name, url, user_name, user_email):
    # TODO: Set admin locale. Admin/user locale is stored at drupal database so may be a bit challenging to fetch it. We default to finnish for the time being
    current_locale = get_lang()
    i18n.set_lang("fi")

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
    finally:
        set_lang(current_locale)


def mail_process_status(locale, member_user, approve, group_name, capacity):
    current_locale = get_lang()
    if locale == 'en':
        _reset_lang()
    else:
        set_lang(locale)

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
    finally:
        set_lang(current_locale)


def _reset_lang():
    try:
        i18n.set_lang(None)
    except TypeError:
        pass
