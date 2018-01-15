# -*- coding: utf-8 -*-

import uuid
import os

from ckan import model
from ckan.lib import celery_app
from ckan.lib.cli import CkanCommand

from ckanext.ytp_tasks.model import YtpTaskSource, YtpTaskTables

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


@celery_app.celery.task(name="ckanext.ytp_tasks.execute_all")
def execute_all(stage=None):
    """ Execute all tasks from database """
    _load_config()
    YtpTaskTables.init()
    session = model.Session
    query = session.query(YtpTaskSource).filter(YtpTaskSource.active == True)  # noqa
    if stage is not None:
        query = query.filter(YtpTaskSource.frequency == stage)

    for task in query.all():
        celery_app.celery.send_task(task.task, args=(unicode(task.data),), task_id=str(uuid.uuid4()))
