import paste.fixture
import pylons.test

from ckan.tests import TestCase
from ckan import model, plugins, tests
from ckan.plugins import toolkit
from ckan.model.package import Package
from ckanext.ytp.common.converters import is_url, to_list_json, from_json_list
from ckan.lib.navl.dictization_functions import Invalid
from pylons import config
from paste.deploy.converters import asbool


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
        context['auth_user_obj'] = model.User.get(admin_user['name'])
        return context

    def test_create_dataset(self):
        context = self._create_context()
        data_dict = {'name': 'test_dataset_1', 'title': 'test_title', 'notes': "test_notes", 'license_id': "licence_id",
                     'content_type': "content_type_test", 'tag_string': "tag1,tag2", 'collection_type': 'Open Data',
                     'copyright_notice': 'test_notice'}

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

    def test_api_create_dataset(self):
        tests.call_action_api(self.app, 'package_create', status=409, name='test-name-1', title="test-title-1", content_type="test1,test2",
                              license_id="other", notes="test notes", tag_string="tag1,tag2", apikey=self.sysadmin.apikey)

        tests.call_action_api(self.app, 'package_create', status=200, name='test-name-2', title="test-title-2", content_type="test1,test2",
                              license_id="other", notes="test notes", tag_string="tag1,tag2", collection_type="Open Data", apikey=self.sysadmin.apikey)

        test_dataset = Package.get('test-name-2')
        self.assert_equal(test_dataset.maintainer, "")
        self.assert_equal(test_dataset.maintainer_email, "")

        if not asbool(config.get('ckanext.ytp.dataset.auto_author', False)):
            self.assert_equal(test_dataset.author, "")
            self.assert_equal(test_dataset.author_email, "")
