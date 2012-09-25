import os
import shutil
import tempfile
import subprocess
import time
import requests
from datetime import datetime, timedelta
from nose.tools import raises
from functools import wraps
import json
from urllib import quote_plus
from pylons import config
from ckan import model
from ckan import plugins
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.tests import BaseCase, url_for, CreateTestData
from nose.tools import assert_raises

from ckanext.archiver.tasks import (link_checker, 
                                    update,
                                    download,
                                    ArchiverError,
                                    DownloadError,
                                    ChooseNotToDownload,
                                    LinkCheckerError, 
                                    CkanError,
                                   )

from mock_remote_server import MockEchoTestServer


def with_mock_url(url=''):
    """
    Start a MockEchoTestServer call the decorated function with the server's address prepended to ``url``.
    """
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            with MockEchoTestServer().serve() as serveraddr:
                return func(*(args + ('%s/%s' % (serveraddr, url),)), **kwargs)
        return decorated
    return decorator


class TestLinkChecker(BaseCase):
    """
    Tests for link checker task
    """

    @classmethod
    def setup_class(cls):
        plugins.unload_all()
        cls._saved_plugins_config = config.get('ckan.plugins', '')
        config['ckan.plugins'] = 'archiver'
        plugins.load_all(config)

    @classmethod
    def teardown_class(cls):
        plugins.unload_all()
        config['ckan.plugins'] = cls._saved_plugins_config
        plugins.load_all(config)

    def test_file_url(self):
        url = u'file:///home/root/test.txt'
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    def test_bad_url(self):
        url = u'file:///home/root/test.txt'
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    def test_bad_query_string(self):
        url = u'http://uk.sitestat.com/homeoffice/rds/s?' \
            + u'rds.hosb0509tabsxls&ns_type=pdf&ns_url=' \
            + u'[http://www.homeoffice.gov.uk/rds/pdfs09/hosb0509tabs.xls'
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    @with_mock_url('+/http://www.homeoffice.gov.uk/publications/science-research-statistics/research-statistics/drugs-alcohol-research/hosb1310/hosb1310-ann2tabs?view=Binary')
    def test_non_escaped_url(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        res = link_checker(context, data)
        assert res

    def test_empty_url(self):
        url =  u''
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    @with_mock_url('?status=503')
    def test_url_with_503(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    @with_mock_url('?status=404')
    def test_url_with_404(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkCheckerError, link_checker, context, data)

    @with_mock_url('')
    def test_url_with_30x_follows_redirect(self, url):
        redirect_url = url + u'?status=200&content=test&content-type=text/csv'
        url += u'?status=301&location=%s' % quote_plus(redirect_url)
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result

    @with_mock_url('?status=200')
    def test_good_url(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result


class TestArchiver(BaseCase):
    """
    Tests for Archiver task
    """

    @classmethod
    def setup_class(cls):
        cls.temp_dir = tempfile.mkdtemp()

        fake_ckan_path = os.path.join(os.path.dirname(__file__), "fake_ckan.py")
        cls.fake_ckan = subprocess.Popen(['python', fake_ckan_path])
        cls.fake_ckan_url = 'http://0.0.0.0:50001'

        #make sure services are running
        for i in range(0, 12):
            time.sleep(0.1)
            response = requests.get(cls.fake_ckan_url)
            if response:
                break
        else:
            raise Exception('services did not start!')

        cls.fake_context = {
            'site_url': cls.fake_ckan_url,
            'apikey': u'fake_api_key',
            'site_user_apikey': u'fake_site_user_api_key',
        }
        cls.fake_resource = {
            'id': u'fake_resource_id',
            'revision_id': u'fake_revision_id',
            'url': cls.fake_ckan_url,
            'format': 'csv'
        }

    @classmethod
    def teardown_class(cls):
        os.removedirs(cls.temp_dir)
        cls.fake_ckan.kill()

    def _remove_archived_file(self, file_path):
        if file_path:
            if os.path.exists(file_path):
                resource_folder = os.path.split(file_path)[0]
                if 'fake_resource_id' in resource_folder:
                    shutil.rmtree(resource_folder)

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_resource_hash_and_content_length(self, url):
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['url'] = url
        data = json.dumps(resource)
        result = json.loads(update(context, data))

        assert result['resource']['size'] == unicode(len('test'))
        from hashlib import sha1
        assert result['resource']['hash'] == sha1('test').hexdigest(), result
        self._remove_archived_file(result.get('file_path'))

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_archived_file(self, url):
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['url'] = url
        data = json.dumps(resource)
        result = json.loads(update(context, data))

        assert result['file_path']
        assert os.path.exists(result['file_path'])

        with open(result['file_path']) as f:
            content = f.readlines()
            assert len(content) == 1
            assert content[0] == "test"

        self._remove_archived_file(result.get('file_path'))

    @with_mock_url('?content-type=arfle-barfle-gloop')
    def test_download_url_with_unknown_content_type(self, url):
        resource = self.fake_resource
        resource['format'] = 'arfle-barfle-gloop'
        resource['url'] = url
        assert_raises(ChooseNotToDownload, download, self.fake_context, resource)

    @with_mock_url('?content-type=arfle-barfle-gloop')
    def test_update_url_with_unknown_content_type(self, url):
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['format'] = 'arfle-barfle-gloop'
        resource['url'] = url
        data = json.dumps(resource)
        result = update(context, data)
        assert not result, result

    @with_mock_url('?content=test&content-type=arfle-barfle-gloop')
    def test_update_all_content_types(self, url):
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['format'] = 'arfle-barfle-gloop'
        resource['url'] = url
        data = json.dumps(resource)
        from ckanext.archiver import default_settings
        tmp = default_settings.DATA_FORMATS
        default_settings.DATA_FORMATS = 'all'
        try:
            result = update(context, data)
        finally:
            default_settings.DATA_FORMATS = tmp

    @with_mock_url('?status=200&content-type=csv')
    def test_update_with_zero_length(self, url):
        # i.e. no content
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['format'] = 'arfle-barfle-gloop'
        resource['url'] = url
        data = json.dumps(resource)
        result = update(context, data)
        assert not result, result

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_download_file(self, url):
        context = json.dumps(self.fake_context)
        resource = self.fake_resource
        resource['url'] = url

        result = download(self.fake_context, resource)

        assert result['saved_file']
        assert os.path.exists(result['saved_file'])
        self._remove_archived_file(result.get('saved_file'))

        # Modify the resource and check that the resource size gets updated
        resource['url'] = url.replace('content=test','content=test2')
        result = download(self.fake_context, resource)
        assert resource['size'] == unicode(len('test2')), resource['size']

        self._remove_archived_file(result.get('saved_file'))


