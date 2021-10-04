# encoding: utf-8
'''Tests for the ckanext.ytp_tasks extension.
'''


import pytest
import ckan.model as model
import ckan.tests.helpers as helpers
from ckanext.ytp_tasks.model import YtpTaskTables


@pytest.mark.usefixtures("clean_db")
class TestYtpTasksPlugin():
    def test_ytp_tasks_add(self):
        """ Test adding tasks source via API. """

        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()
        YtpTaskTables.create_tables()

        with pytest.raises(Exception):
            helpers.call_action('ytp_tasks_add')

        with pytest.raises(KeyError):
            helpers.call_action('ytp_tasks_add', apikey=self.sysadmin.apikey)

        data = {'id': 'test1', 'task': 'test-task', 'data': 'test-data', 'frequency': "HOURLY"}

        helpers.call_action('ytp_tasks_add', apikey=self.sysadmin.apikey, **data)

        with pytest.raises(Exception):
            helpers.call_action('ytp_tasks_add', **data)
