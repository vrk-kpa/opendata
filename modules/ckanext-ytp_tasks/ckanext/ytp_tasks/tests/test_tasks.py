# encoding: utf-8
'''Tests for the ckanext.ytp_tasks extension.
'''


import pytest
import ckan.model as model
from ckanext.ytp_tasks.tasks import execute_all
from ckanext.ytp_tasks.model import YtpTaskTables


@pytest.mark.usefixtures("clean_db")
class TestTasks():
    def test_execute_all(self):
        """ Simply test execution of all tasks """
        # Does not contain any tasks in database

        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()
        YtpTaskTables.create_tables()
        result = execute_all()
        assert result is None
