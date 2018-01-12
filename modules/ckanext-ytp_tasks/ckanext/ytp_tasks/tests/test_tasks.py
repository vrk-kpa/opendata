import paste.fixture
import pylons.test
from ckan import model
from ckan.tests import TestCase
from ckanext.ytp_tasks.tasks import execute_all
from ckanext.ytp_tasks.model import YtpTaskTables


class TestTasks(TestCase):
    """ Test tasks """

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

    def test_execute_all(self):
        """ Simply test execution of all tasks """
        # Does not contain any tasks in database
        result = execute_all.apply()
        self.assert_true(result.successful())
