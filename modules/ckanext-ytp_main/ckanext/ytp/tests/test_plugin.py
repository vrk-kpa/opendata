# -*- coding: utf-8 -*-
import paste.fixture
import pylons.test
import simplejson

from ckan import model, plugins, tests
from ckan.lib.munge import munge_title_to_name
from ckan.lib.navl.dictization_functions import Invalid
from ckan.logic import NotFound
from ckan.model.package import Package
from ckan.plugins import toolkit
from ckan.tests import TestCase
from paste.deploy.converters import asbool
from pylons import config

import tools
from ckanext.ytp.converters import is_url, to_list_json, from_json_list
from ckanext.ytp.tasks import organization_import

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

        if not asbool(config.get('ckanext.ytp.auto_author', False)):
            self.assert_equal(test_dataset.author, "")
            self.assert_equal(test_dataset.author_email, "")


class TestYtpOrganizationPlugin(TestCase):
    """ Test YtpOrganizationPlugin class """

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

    def test_create_unique_organizations(self):
        """ Test duplicate title name """
        tests.call_action_api(self.app, 'organization_create', name='test-name-1',
                              title="test-title", apikey=self.sysadmin.apikey)
        tests.call_action_api(self.app, 'organization_create', status=409, name='test-name-2',
                              title="test-title", apikey=self.sysadmin.apikey)

    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        return context

    def test_user_create_hook(self):
        self.assert_raises(NotFound, plugins.toolkit.get_action('organization_show'), self._create_context(), {"id": "yksityishenkilo"})

        plugins.toolkit.get_action('user_create')(self._create_context(), {"name": "test_create_1", "id": "test_create_1",
                                                                           "email": "example1@localhost", "password": "test_password",
                                                                           "fullname": "test_fullname_1"})
        plugins.toolkit.get_action('user_create')(self._create_context(), {"name": "test_create_2", "id": "test_create_2",
                                                                           "email": "example2@localhost", "password": "test_password",
                                                                           "fullname": "test_fullname_2"})
        plugins.toolkit.get_action('user_update')(self._create_context(), {"id": "test_create_2", "id": "test_create_2",
                                                                           "email": "example3@localhost", "password": "test_password",
                                                                           "fullname": "test_fullname_3"})

    def test_organization_import(self):
        """ Test organization import """
        organization_url = tools.get_organization_test_source()
        data = simplejson.dumps({'url': organization_url, 'public_organization': True})
        for _ in xrange(2):
            result = organization_import.apply((data,))
            self.assert_true(result.successful())
            for title in u"Kainuun ty\u00f6- ja elinkeinotoimisto", u"Lapin ty\u00f6- ja elinkeinotoimisto", u"Suomen ymp\u00e4rist\u00f6keskus":
                organization = tests.call_action_api(self.app, 'organization_show', id=munge_title_to_name(title).lower())
                self.assert_equal(organization['title'], title)
                public_org = 'false'
                for extra in organization['extras']:
                    if extra['key'] == 'public_adminstration_organization':
                        public_org = 'true'
                self.assert_equal(public_org, 'true')

    def test_organization_import_update(self):
        """ Test updating organization import from file """
        organization_url = tools.get_organization_test_source()

        for extras in False, True:
            data = {'url': organization_url}
            if extras:
                data['public_organization'] = True
            result = organization_import.apply((simplejson.dumps(data),))
            self.assert_true(result.successful())
            for title in u"Kainuun ty\u00f6- ja elinkeinotoimisto", u"Lapin ty\u00f6- ja elinkeinotoimisto", u"Suomen ymp\u00e4rist\u00f6keskus":
                organization = tests.call_action_api(self.app, 'organization_show', id=munge_title_to_name(title).lower())
                self.assert_equal(organization['title'], title)
                self.assert_true('public_adminstration_organization' not in organization)  # We do not want this to be updated

    def test_organization_import_with_name(self):
        """ Test organization import """
        expected = (u"hri", u"Ulkoinen lähde: Hri.fi", u"Tähän organisaatioon harvestoidaan tietoaineistoja Helsinki Region Infosharesta."), \
                   (u"datagovuk", u"Data.Gov.UK", u"")
        organization_url = tools.get_organization_harvest_test_source()
        data = simplejson.dumps({'url': organization_url})
        for _ in xrange(2):
            result = organization_import.apply((data,))
            self.assert_true(result.successful())
            for name, title, description in expected:
                organization = tests.call_action_api(self.app, 'organization_show', id=name)
                self.assert_equal(organization['title'], title)
                self.assert_equal(organization['description'], description)
                self.assert_true('public_adminstration_organization' not in organization)


class TestYtpUserPlugin(TestCase):
    """ Test YtpUserPlugin class """

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

    def _create_context(self, user_object):
        return {'model': model, 'session': model.Session, 'user': user_object.name, 'user_obj': user_object}

    def _create_user(self, name, fullname):
        user = model.User(name=name, email="test@example.com", fullname=fullname)
        model.Session.add(user)
        model.Session.commit()
        return user

    def test_user_update(self):
        user_object = self._create_user('tester', 'test tester')
        context = self._create_context(user_object)

        data_dict = {'id': user_object.name, 'email': user_object.email, 'fullname': user_object.fullname}
        toolkit.get_action('user_update')(context, data_dict)

        data_dict = {'id': user_object.name, 'email': user_object.email, 'fullname': user_object.fullname}
        data_dict_extras = {'facebook': 'http://example.com/facebook', 'job_title': 'tester', 'telephone_number': '+358 123 1234',
                            'image_url': 'http://example.com/me.png', 'linkedin': 'http://example.com/linkedin',
                            'twitter': 'http://example.com/twitter'}
        data_dict.update(data_dict_extras)

        from pprint import pprint
        pprint(data_dict)
        user_data = toolkit.get_action('user_update')(context, data_dict)
        user_show_data = toolkit.get_action('user_show')(context, {'id': user_object.name})
        updated_user = model.User.get('tester')

        for key, value in data_dict_extras.iteritems():
            self.assert_equal(user_data[key], value)
            self.assert_equal(user_show_data[key], value)
            self.assert_equal(updated_user.extras[key], value)
