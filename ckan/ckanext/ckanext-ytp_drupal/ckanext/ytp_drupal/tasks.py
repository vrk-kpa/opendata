# -*- coding: utf-8 -*-

import os

from ckan import model
from ckan.lib import celery_app
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

_config_loaded = False


class FakeOptions():
    """ Fake options for fake command """
    config = os.environ.get('CKAN_CONFIG')


def _load_config():
    # We want CKAN environment loaded. Here we fake that this is a CKAN command.
    global _config_loaded
    if _config_loaded:
        return
    _config_loaded = True

    command = CkanCommand(None)
    command.options = FakeOptions()
    command._load_config()


def _create_context():
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    admin_user = toolkit.get_action('get_site_user')(context, None)
    context['user'] = admin_user['name']
    context['auth_user_obj'] = admin_user
    return context


@celery_app.celery.task(name="ckanext.ytp_drupal.delete_user")
def delete_user(user_id):
    """ Execute all tasks from database """
    _load_config()
    toolkit.get_action('user_delete')(_create_context(), {'id': user_id})
