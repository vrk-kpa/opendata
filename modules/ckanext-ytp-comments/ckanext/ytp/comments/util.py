from lxml.html.clean import Cleaner, autolink_html
from ckan.lib.mailer import mail_user, MailerException
from ckan.lib import helpers
from pylons import config
import ckan.plugins.toolkit as toolkit
from ckan.lib.base import model
from ckan.lib.i18n import set_lang, get_lang
from ckan.common import _, c, g
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

def send_comment_notification_mail(recipient, dataset, comment):

    from ckanext.ytp.comments import email_template

    """
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    parent_id = Column(types.UnicodeText, ForeignKey('comment.id'))
    children = relationship("Comment", lazy="joined", join_depth=10,
                            backref=backref('parent', remote_side=[id]),
                            order_by="asc(Comment.creation_date)")

    thread_id = Column(types.UnicodeText, ForeignKey('comment_thread.id'), nullable=True)
    user_id = Column(types.UnicodeText, ForeignKey(model.User.id), nullable=False)
    subject = Column(types.UnicodeText)
    comment = Column(types.UnicodeText)

    creation_date = Column(types.DateTime, default=datetime.datetime.now)
    modified_date = Column(types.DateTime)
    approval_status = Column(types.UnicodeText)

    state = Column(types.UnicodeText, default=u'active')
    """

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
        user_email = model.User.get(comment.user_id).email

    subject = _(email_template.subject) % {
        'dataset': dataset.title
    }
    message = _(email_template.message) % {
        'user': recipient.name,
        'email': user_email,
        'dataset': dataset.title,
        'link': url,
        'comment_subject': helpers.markdown_extract(comment.subject).strip(),
        'comment': helpers.markdown_extract(comment.comment).strip()
    }

    # Finally mail the user and reset locale

    try:
        mail_user(recipient, subject, message)
    except MailerException, e:
        log.error(e)
    finally:
        set_lang(current_locale)
