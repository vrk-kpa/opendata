import os
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

from ckanext.archiver.tasks import link_checker
from mock_remote_server import MockEchoTestServer

# TEST_ARCHIVE_FOLDER = 'tests/test_archive_folder'

# make sure test archive folder exists
# if not os.path.exists(TEST_ARCHIVE_FOLDER):
#     os.mkdir(TEST_ARCHIVE_FOLDER)

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
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'Invalid url scheme', result

    def test_bad_url(self):
        url = u'file:///home/root/test.txt'
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'Invalid url scheme', result

    def test_bad_query_string(self):
        url = u'http://uk.sitestat.com/homeoffice/rds/s?' \
            + u'rds.hosb0509tabsxls&ns_type=pdf&ns_url=' \
            + u'[http://www.homeoffice.gov.uk/rds/pdfs09/hosb0509tabs.xls'
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'Invalid URL', result

    def test_empty_url(self):
        url =  u''
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'Invalid url scheme', result

    @with_mock_url('?status=503')
    def test_url_with_503(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'Service unavailable', result

    @with_mock_url('?status=404')
    def test_url_with_404(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == False, result
        assert result['error_message'] == 'URL unobtainable', result

    @with_mock_url('')
    def test_url_with_30x_follows_redirect(self, url):
        redirect_url = url + u'?status=200&content=test&content-type=text/csv'
        url += u'?status=301&location=%s' % quote_plus(redirect_url)
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == True, result

    @with_mock_url('?status=200')
    def test_good_url(self, url):
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result['success'] == True, result


class TestArchiver(BaseCase):
    """
    Tests for link checker task
    """

    pass

    # @with_mock_url('?status=200;content=test;content-type=text/csv')
    # def test_resource_hash_and_content_length(self, url):
    #     context = json.dumps({})
    #     data = json.dumps({'url': url})
    #     result = json.loads(link_checker(context, data))
    #     assert result['success'] == True, result
    #     assert result['content_length'] == unicode(len('test'))
    #     from hashlib import sha1
    #     assert result['hash'] == sha1('test').hexdigest(), result

    # @with_mock_url('?content-type=arfle-barfle-gloop')
    # def test_url_with_unknown_content_type(self, url):
    #     context = json.dumps({})
    #     data = json.dumps({'url': url})
    #     result = json.loads(link_checker(context, data))
    #     assert result['success'] == False, result
    #     assert result['error_message'] == 'unrecognised content type', result

