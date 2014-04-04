import httplib
from unittest import TestCase

from ckan.config.middleware import make_app
from paste.deploy import appconfig
import paste.fixture
from ckan.tests import conf_dir, url_for, CreateTestData

from mockgoogleanalytics import runmockserver
from ckanext.googleanalytics.commands import LoadAnalytics
from ckanext.googleanalytics.commands import InitDB
from ckanext.googleanalytics import dbutil
import ckanext.googleanalytics.gasnippet as gasnippet


class MockClient(httplib.HTTPConnection):
    def request(self, http_request):
        filters = http_request.uri.query.get('filters')
        path = http_request.uri.path
        if filters:
            if "dataset" in filters:
                path += "/dataset"
            else:
                path += "/download"
        httplib.HTTPConnection.request(self, http_request.method, path)
        resp = self.getresponse()
        return resp


class TestConfig(TestCase):
    def test_config(self):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'googleanalytics'
        config.local_conf['googleanalytics.id'] = ''
        command = LoadAnalytics("loadanalytics")
        command.CONFIG = config.local_conf
        self.assertRaises(Exception, command.run, [])


class TestLoadCommand(TestCase):
    @classmethod
    def setup_class(cls):
        InitDB("initdb").run([])  # set up database tables

        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'googleanalytics'
        config.local_conf['googleanalytics.username'] = 'borf'
        config.local_conf['googleanalytics.password'] = 'borf'
        config.local_conf['googleanalytics.id'] = 'UA-borf-1'
        config.local_conf['googleanalytics.show_downloads'] = 'true'
        cls.config = config.local_conf
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        env = {'HTTP_ACCEPT': ('text/html;q=0.9,text/plain;'
                               'q=0.8,image/png,*/*;q=0.5')}
        cls.app = paste.fixture.TestApp(wsgiapp, extra_environ=env)
        CreateTestData.create()
        runmockserver()

    @classmethod
    def teardown_class(cls):
        CreateTestData.delete()
        conn = httplib.HTTPConnection("localhost:%d" % 6969)
        conn.request("QUIT", "/")
        conn.getresponse()

    def test_analytics_snippet(self):
        response = self.app.get(url_for(controller='tag', action='index'))
        code = gasnippet.header_code % (self.config['googleanalytics.id'],
                                        'auto')
        assert code in response.body

    def test_top_packages(self):
        command = LoadAnalytics("loadanalytics")
        command.TEST_HOST = MockClient('localhost', 6969)
        command.CONFIG = self.config
        command.run([])
        packages = dbutil.get_top_packages()
        resources = dbutil.get_top_resources()
        self.assertEquals(packages[0][1], 2)
        self.assertEquals(resources[0][1], 4)

    def test_download_count_inserted(self):
        command = LoadAnalytics("loadanalytics")
        command.TEST_HOST = MockClient('localhost', 6969)
        command.CONFIG = self.config
        command.run([])
        response = self.app.get(url_for(
            controller='package', action='read', id='annakarenina'
        ))
        assert "[downloaded 4 times]" in response.body

    def test_js_inserted_resource_view(self):
        from nose import SkipTest
        raise SkipTest("Test won't work until CKAN 1.5.2")

        from ckan.logic.action import get
        from ckan import model
        context = {'model': model, 'ignore_auth': True}
        data = {'id': 'annakarenina'}
        pkg = get.package_show(context, data)
        resource_id = pkg['resources'][0]['id']

        command = LoadAnalytics("loadanalytics")
        command.TEST_HOST = MockClient('localhost', 6969)
        command.CONFIG = self.config
        command.run([])
        response = self.app.get(url_for(
            controller='package', action='resource_read', id='annakarenina',
            resource_id=resource_id
        ))
        assert 'onclick="javascript: _gaq.push(' in response.body
