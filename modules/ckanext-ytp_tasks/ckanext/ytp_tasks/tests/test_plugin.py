from ckan.tests import TestCase
import paste.fixture
import pylons.test
import ckan.model as model
import ckan.tests as tests
from ckanext.ytp_tasks.model import YtpTaskTables


class TestYtpTasksPlugin(TestCase):
    """ Test YtpTasksPlugin class """

    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)

    def setup(self):
        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()
        YtpTaskTables.create_tables()

    def teardown(self):
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        pass

    def test_ytp_tasks_add(self):
        """ Test adding organization source via API. """
        self.assert_raises(Exception, tests.call_action_api, self.app, 'ytp_tasks_add')
        self.assert_raises(KeyError, tests.call_action_api, self.app, 'ytp_tasks_add', apikey=self.sysadmin.apikey)

        data = {'id': 'test1', 'task': 'test-task', 'data': 'test-data', 'frequency': "HOURLY"}

        tests.call_action_api(self.app, 'ytp_tasks_add', apikey=self.sysadmin.apikey, **data)
        self.assert_raises(Exception, tests.call_action_api, self.app, 'ytp_tasks_add', **data)
