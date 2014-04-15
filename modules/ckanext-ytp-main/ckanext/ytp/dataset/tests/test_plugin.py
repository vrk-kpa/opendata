import paste.fixture
import pylons.test

from ckan.tests import TestCase
from ckan import model, plugins
from ckan.plugins import toolkit
from ckan.model.package import Package
from ckanext.ytp.common.converters import is_url, to_list_json, from_json_list
from ckan.lib.navl.dictization_functions import Invalid


class TestYtpDatasetPlugin(TestCase):
    """ Test YtpDatsetPlugin class """

    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)

    def setup(self):
        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()

    def teardown(self):
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        pass

    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        return context

    def test_create_dataset(self):
        context = self._create_context()
        data_dict = {'name': 'test_dataset_1', 'extras': [{'key': 'copyright_notice', 'value': 'test_notice'}]}

        result = toolkit.get_action('package_create')(context, data_dict)

        self.assert_equal(result['name'], 'test_dataset_1')
        test_dataset = Package.get('test_dataset_1')

        self.assert_equal(test_dataset.extras['copyright_notice'], 'test_notice')

    def test_is_url(self):
        """ test is_url validator """
        context = {}
        is_url("http://www.example.com", context)
        is_url("http://www.example.com/path", context)
        self.assert_raises(Invalid, is_url, "test_fail", context)
        self.assert_raises(Invalid, is_url, "/test/test", context)
        self.assert_raises(Invalid, is_url, "//test/test", context)

    def test_to_list_json(self):
        """ test to_list_json converter """
        context = {}
        self.assert_equal(to_list_json("test_value", context).replace(' ', ''), '["test_value"]')
        self.assert_equal(to_list_json(["test_value1", "test_value2"], context).replace(' ', ''), '["test_value1","test_value2"]')

    def test_from_json_list(self):
        """ test from_json_list converter """
        context = {}
        self.assert_equal(from_json_list("test_value", context), ["test_value"])
        self.assert_equal(from_json_list('["test_value1","test_value2"]', context), ["test_value1", "test_value2"])
