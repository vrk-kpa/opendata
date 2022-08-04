# -*- coding: utf-8 -*-


import os
import six
from ckan import model
import ckan.lib.jobs as jobs
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


def execute_all(stage=None):
    """ Execute all tasks from database """
    _load_config()
    YtpTaskTables.init()
    session = model.Session
    query = session.query(YtpTaskSource).filter(YtpTaskSource.active == True)  # noqa
    if stage is not None:
        query = query.filter(YtpTaskSource.frequency == stage)

    for task in query.all():
        jobs.enqueue(task.task, [six.text_type(task.data)])
