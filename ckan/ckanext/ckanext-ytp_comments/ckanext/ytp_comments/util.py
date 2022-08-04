from lxml.html.clean import Cleaner, autolink_html
from flask_babel import force_locale
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.lib import helpers
import ckan.plugins.toolkit as toolkit
from ckan.lib.base import model
from ckan.common import g

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

    with force_locale(_get_safe_locale()):
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

        try:
            mail_recipient(recipient_name, recipient_email, subject, message)
        except MailerException as e:
            log.error(e)
