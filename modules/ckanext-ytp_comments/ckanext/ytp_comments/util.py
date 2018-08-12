from lxml.html.clean import Cleaner, autolink_html
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.lib import helpers
import ckan.plugins.toolkit as toolkit
from ckan.lib.base import model
from ckan.lib.i18n import set_lang, get_lang
from ckan.common import g
from pylons import i18n

import logging
log = logging.getLogger(__name__)

ALLOWED_TAGS = [
    "a", "em", "strong", "cite", "code", "ul", "ol", "li", "p", "blockquote"
]


def clean_input(comment):
    data = comment
    if 'href' not in data:
        data = autolink_html(data, avoid_elements=['a'])

    cleaner = Cleaner(add_nofollow=True, allow_tags=ALLOWED_TAGS,
                      remove_unknown_tags=False)
    content = cleaner.clean_html(data).replace('\n', '<br/>')
    return content


def _reset_lang():
    try:
        i18n.set_lang(None)
    except TypeError:
        pass


def _get_safe_locale():
    return helpers.lang()


def send_comment_notification_mail(recipient_name, recipient_email, dataset, comment):

    from ckanext.ytp_comments import email_template

    # Fill out the message template

    url = str(g.site_url) + toolkit.url_for(controller='package', action='read', id=dataset.id)

    if comment.user_id:
        userobj = model.User.get(comment.user_id)
        commenter_email = userobj.email
        commenter_name = userobj.name

    subject_vars = {
        'dataset': dataset.title
    }
    subject = email_template.subject.format(**subject_vars)

    message_vars = {
        'user': commenter_name,
        'email': commenter_email,
        'dataset': dataset.title,
        'link': url,
        'comment_subject': helpers.markdown_extract(comment.subject).strip(),
        'comment': helpers.markdown_extract(comment.comment).strip()
    }
    message = email_template.message.format(**message_vars)

    log.debug(subject)
    log.debug(message)

    # Locale fix
    current_locale = get_lang()
    locale = _get_safe_locale()

    if locale == 'en':
        _reset_lang()
    else:
        set_lang(locale)
    # Finally mail the user and reset locale

    try:
        log.debug("LOCALE: " + str(locale))
        log.debug(subject)
        log.debug(message)

        mail_recipient(recipient_name, recipient_email, subject, message)
    except MailerException, e:
        log.error(e)
    finally:
        set_lang(current_locale)
