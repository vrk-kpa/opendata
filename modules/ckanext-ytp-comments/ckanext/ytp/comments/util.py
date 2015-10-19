from lxml.html.clean import Cleaner, autolink_html
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.lib import helpers
from pylons import config
import ckan.plugins.toolkit as toolkit
from ckan.lib.base import model
from ckan.lib.i18n import set_lang, get_lang
from ckan.common import _, g
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
    try:
        return helpers.lang()
    except:
        return config.get('ckan.locale_default', 'en')


def send_comment_notification_mail(recipient_name, recipient_email, dataset, comment):

    from ckanext.ytp.comments import email_template

    # Locale fix
    current_locale = get_lang()
    locale = _get_safe_locale()

    if locale == 'en':
        _reset_lang()
    else:
        set_lang(locale)

    # Fill out the message template

    url = str(g.site_url) + toolkit.url_for(controller='package', action='read', id=dataset.id)

    if comment.user_id:
        userobj = model.User.get(comment.user_id)
        commenter_email = userobj.email
        commenter_name = userobj.name

    subject = _(email_template.subject) % {
        'dataset': dataset.title
    }

    message = _(email_template.message) % {
        'user': commenter_name,
        'email': commenter_email,
        'dataset': dataset.title,
        'link': url,
        'comment_subject': helpers.markdown_extract(comment.subject).strip(),
        'comment': helpers.markdown_extract(comment.comment).strip()
    }

    # Finally mail the user and reset locale

    try:
        mail_recipient(recipient_name, recipient_email, subject, message)
    except MailerException, e:
        log.error(e)
    finally:
        set_lang(current_locale)
