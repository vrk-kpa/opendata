import logging
from pylons import config
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.logic import get_action
from ckan.lib.base import render_jinja2

log = logging.getLogger(__name__)


def send_organization_approved(organization):
    from ckan import model

    context = {'model': model, 'ignore_auth': True, 'session': model.Session}
    site_addr = config['ckan.site_url']

    user_id = organization['users'][0]['id']
    user_details = get_action('user_show')(context, data_dict={"id": user_id})

    email = make_email_template('organization_approved', {
      "url_guide": site_addr + '/opas/avoimen-datan-opas',
      "url_user_guide": site_addr + '/opas/johdanto'
    })

    try:
        mail_recipient(
            user_details['name'],
            user_details['email'],
            email['subject'],
            email['message'],
            {'Content-Type': 'text/html; charset=UTF-8'}
        )
    except MailerException as e:
        # NOTE: MailerException happens in cypress.
        log.error('Error sending email to user: %s', e)


def send_new_organization_email_to_admin():
    site_addr = config['ckan.site_url']

    email = make_email_template('admin_new_organization', {
      "ckan_admin_url": site_addr + '/data/ckan-admin/organization_management',
    })

    try:
        mail_recipient(
            'admin',
            config['ckan.emails.admin'],
            email['subject'],
            email['message'],
            {'Content-Type': 'text/html; charset=UTF-8'}
        )
    except MailerException as e:
        # NOTE: MailerException happens in cypress.
        log.error('Error sending email to admin: %s', e)


def make_email_template(template, extra_vars):
    message = render_jinja2('emails/message/{0}.html'.format(template), extra_vars)
    subject = render_jinja2('emails/subject/{0}.txt'.format(template), extra_vars)
    return {'message': message, 'subject': subject}
