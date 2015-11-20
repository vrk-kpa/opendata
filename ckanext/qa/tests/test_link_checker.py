import logging
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
from urllib import quote_plus, urlencode
from pylons import config
from ckan import model
from ckan import plugins
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.tests import BaseCase, url_for, CreateTestData
from ckan.tests import TestController as ControllerTestCase
from nose.tools import assert_raises, assert_equal
from ckan.tests import assert_in

from ckanext.archiver.tasks import (link_checker, 
                                    update_package,
                                    download,
                                    ArchiverError,
                                    DownloadError,
                                    ChooseNotToDownload,
                                    LinkCheckerError, 
                                    CkanError,
                                   )

from mock_remote_server import MockEchoTestServer

# enable celery logging for when you run nosetests -s
log = logging.getLogger('ckanext.archiver.tasks')
def get_logger():
    return log
update_package.get_logger = get_logger

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


class TestLinkChecker(ControllerTestCase):
    """
    Tests for link checker task
    """
    def check_link(self, url):
        result = self.app.get('/qa/link_checker?%s' % urlencode({'url': url}))
        return json.loads(result.body)[0]

    @with_mock_url('?status=200')
    def test_url_working_but_formatless(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], None)

    @with_mock_url('file.csv')
    def test_format_by_url_extension(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], 'CSV')

    @with_mock_url('file.csv.zip')
    def test_format_by_url_extension_zipped(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], 'CSV / ZIP')

    @with_mock_url('file.f1.f2')
    def test_format_by_url_extension_unknown(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], 'F1 / F2')

    def test_encoded_url(self):
        # This is not actually a URL, and the encoded letters get
        # interpreted as being in the hostname. But should not cause
        # an exception.
        url = 'Over+\xc2\xa325,000+expenditure+report+April-13'
        result = self.check_link(url)
        assert_equal(result['format'], '')

    @with_mock_url('?status=200;content-type=text/plain')
    def test_format_by_mimetype_txt(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], 'TXT')

    @with_mock_url('?status=200;content-type=text/csv')
    def test_format_by_mimetype_csv(self, url):
        result = self.check_link(url)
        assert_equal(result['format'], 'CSV')

    def test_file_url(self):
        url = u'file:///home/root/test.txt'
        result = self.check_link(url)
        assert_in(u'Invalid url scheme. Please use one of: ftp http https',
                  result['url_errors'])
        #assert_raises(LinkCheckerError, link_checker, context, data)

    def test_empty_url(self):
        url =  u''
        result = self.check_link(url)
        assert_in("URL parsing failure - did not find a host name", result['url_errors'])

    @with_mock_url('?status=503')
    def test_url_with_503(self, url):
        result = self.check_link(url)
        assert_in('Server returned HTTP error status: 503 Service Unavailable', result['url_errors'])

    @with_mock_url('?status=404')
    def test_url_with_404(self, url):
        result = self.check_link(url)
        assert_in('Server returned HTTP error status: 404 Not Found', result['url_errors'])

    # Disabled as doesn't work
    #@with_mock_url('')
    #def test_url_with_30x_follows_redirect(self, url):
    #    redirect_url = url + u'?status=200&content=test&content-type=text/csv'
    #    url += u'?status=301&location=%s' % quote_plus(redirect_url)
    #    result = self.check_link(url)
    #    # The redirect works and the CSV is picked up
    #    assert_equal(result['format'], 'CSV')

    # e.g. "http://www.dasa.mod.uk/applications/newWeb/www/index.php?page=48&thiscontent=180&date=2011-05-26&pubType=1&PublishTime=09:30:00&from=home&tabOption=1"
    @with_mock_url('?time=09:30&status=200')
    def test_colon_in_query_string(self, url):
        # accept, because browsers accept this
        # see discussion: http://trac.ckan.org/ticket/318
        result = self.check_link(url)
        print result
        assert_equal(result['url_errors'], [])

    @with_mock_url('?status=200 ')
    def test_trailing_whitespace(self, url):
        # accept, because browsers accept this
        result = self.check_link(url)
        print result
        assert_equal(result['url_errors'], [])
