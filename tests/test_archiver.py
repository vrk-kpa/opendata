import logging
import os
import shutil
import tempfile
from functools import wraps
import json
import mock

from urllib import quote_plus
from pylons import config
from nose.tools import assert_raises, assert_equal

from ckan import model
from ckan import plugins
from ckan.tests import BaseCase
from ckan.logic import get_action
try:
    from ckan.tests.helpers import reset_db
    from ckan.tests import factories as ckan_factories
except ImportError:
    from ckan.new_tests.helpers import reset_db
    from ckan.new_tests import factories as ckan_factories

from ckanext.archiver import model as archiver_model
from ckanext.archiver.model import Archival


from ckanext.archiver.tasks import (link_checker,
                                    update_resource,
                                    update_package,
                                    download,
                                    api_request,
                                    DownloadError,
                                    ChooseNotToDownload,
                                    LinkCheckerError,
                                    LinkInvalidError,
                                    CkanError,
                                    response_is_an_api_error
                                    )

from mock_remote_server import MockEchoTestServer, MockWmsServer, MockWfsServer


# enable celery logging for when you run nosetests -s
log = logging.getLogger('ckanext.archiver.tasks')
def get_logger():
    return log
update_resource.get_logger = get_logger
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


class TestLinkChecker(BaseCase):
    """
    Tests for link checker task
    """

    @classmethod
    def setup_class(cls):
        reset_db()
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
        url = u'file:///home/root/test.txt' # schema not allowed
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkInvalidError, link_checker, context, data)

    def test_bad_url(self):
        url = u'http:www.buckshealthcare.nhs.uk/freedom-of-information.htm'
        context = json.dumps({})
        data = json.dumps({'url': url})
        assert_raises(LinkInvalidError, link_checker, context, data)

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

    @with_mock_url('?status=405')
    def test_url_with_405(self, url): # 405: method (HEAD) not allowed
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

    # e.g. "http://www.dasa.mod.uk/applications/newWeb/www/index.php?page=48&thiscontent=180&date=2011-05-26&pubType=1&PublishTime=09:30:00&from=home&tabOption=1"
    @with_mock_url('?time=09:30&status=200')
    def test_colon_in_query_string(self, url):
        # accept, because browsers accept this
        # see discussion: http://trac.ckan.org/ticket/318
        context = json.dumps({})
        data = json.dumps({'url': url})
        result = json.loads(link_checker(context, data))
        assert result        

    @with_mock_url('?status=200 ')
    def test_trailing_whitespace(self, url):
        # accept, because browsers accept this
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
    Tests for Archiver 'update_resource'/'update_package' tasks
    """

    @classmethod
    def setup_class(cls):
        reset_db()
        archiver_model.init_tables(model.meta.engine)

        cls.temp_dir = tempfile.mkdtemp()

        cls.config = config.__file__

    @classmethod
    def teardown_class(cls):
        os.removedirs(cls.temp_dir)

    def teardown(self):
        pkg = model.Package.get(u'testpkg')
        if pkg:
            model.repo.new_revision()
            pkg.purge()
            model.repo.commit_and_remove()

    def _test_package(self, url, format=None):
        pkg = {'resources': [
            {'url': url, 'format': format or 'TXT', 'description': 'Test'}
            ]}
        pkg = ckan_factories.Dataset(**pkg)
        return pkg

    def _test_resource(self, url, format=None):
        pkg = self._test_package(url, format)
        return pkg['resources'][0]

    def assert_archival_error(self, error_message_fragment, resource_id):
        archival = Archival.get_for_resource(resource_id)
        if error_message_fragment not in archival.reason:
            print 'ERROR: %s (%s)' % (archival.reason, archival.status)
            raise AssertionError(archival.reason)

    def test_file_url(self):
        res_id = self._test_resource('file:///home/root/test.txt')['id'] # scheme not allowed
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Invalid url scheme', res_id)

    def test_bad_url(self):
        res_id = self._test_resource('http:host.com')['id'] # no slashes
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Failed to parse', res_id)

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_resource_hash_and_content_length(self, url):
        res_id = self._test_resource(url)['id']
        result = json.loads(update_resource(self.config, res_id))
        assert result['size'] == len('test')
        from hashlib import sha1
        assert result['hash'] == sha1('test').hexdigest(), result
        _remove_archived_file(result.get('cache_filepath'))

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_archived_file(self, url):
        res_id = self._test_resource(url)['id']
        result = json.loads(update_resource(self.config, res_id))

        assert result['cache_filepath']
        assert os.path.exists(result['cache_filepath'])

        with open(result['cache_filepath']) as f:
            content = f.readlines()
            assert len(content) == 1
            assert content[0] == "test"

        _remove_archived_file(result.get('cache_filepath'))

    @with_mock_url('?content-type=application/foo&content=test')
    def test_update_url_with_unknown_content_type(self, url):
        res_id = self._test_resource(url, format='foo')['id'] # format has no effect
        result = json.loads(update_resource(self.config, res_id))
        assert result, result
        assert result['mimetype'] == 'application/foo' # stored from the header

    def test_wms_1_3(self):
        with MockWmsServer(wms_version='1.3').serve() as url:
            res_id = self._test_resource(url)['id']
            result = json.loads(update_resource(self.config, res_id))
            assert result, result
            assert result['request_type'] == 'WMS 1.3'
        with open(result['cache_filepath']) as f:
            content = f.read()
            assert '<WMT_MS_Capabilities' in content, content[:1000]
        _remove_archived_file(result.get('cache_filepath'))

    @with_mock_url('?status=200&content-type=csv')
    def test_update_with_zero_length(self, url):
        # i.e. no content
        res_id = self._test_resource(url)['id']
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Content-length after streaming was 0', res_id)

    @with_mock_url('?status=404&content=test&content-type=csv')
    def test_file_not_found(self, url):
        res_id = self._test_resource(url)['id']
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Server reported status error: 404 Not Found', res_id)

    @with_mock_url('?status=500&content=test&content-type=csv')
    def test_server_error(self, url):
        res_id = self._test_resource(url)['id']
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Server reported status error: 500 Internal Server Error', res_id)

    @with_mock_url('?status=200&content=short&length=1000001&content-type=csv')
    def test_file_too_large_1(self, url):
        # will stop after receiving the header
        res_id = self._test_resource(url)['id']
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Content-length 1000001 exceeds maximum allowed value 1000000', res_id)

    @with_mock_url('?status=200&content_long=test_contents_greater_than_the_max_length&no-content-length&content-type=csv')
    def test_file_too_large_2(self, url):
        # no size info in headers - it stops only after downloading the content
        res_id = self._test_resource(url)['id']
        result = update_resource(self.config, res_id)
        assert not result, result
        self.assert_archival_error('Content-length 1000001 exceeds maximum allowed value 1000000', res_id)

    @with_mock_url('?status=200&content=content&length=abc&content-type=csv')
    def test_content_length_not_integer(self, url):
        res_id = self._test_resource(url)['id']
        result = json.loads(update_resource(self.config, res_id))
        assert result, result

    @with_mock_url('?status=200&content=content&repeat-length&content-type=csv')
    def test_content_length_repeated(self, url):
        # listing the Content-Length header twice causes requests to
        # store the value as a comma-separated list
        res_id = self._test_resource(url)['id']
        result = json.loads(update_resource(self.config, res_id))
        assert result, result

    @with_mock_url('')
    def test_url_with_30x_follows_and_records_redirect(self, url):
        redirect_url = url + u'?status=200&content=test&content-type=text/csv'
        url += u'?status=301&location=%s' % quote_plus(redirect_url)
        res_id = self._test_resource(url)['id']
        result = json.loads(update_resource(self.config, res_id))
        assert result
        assert_equal(result['url_redirected_to'], redirect_url)

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_ipipe_notified(self, url):
        testipipe = plugins.get_plugin('testipipe')
        testipipe.reset()

        res_id = self._test_resource(url)['id']

        # celery.send_task doesn't respect CELERY_ALWAYS_EAGER
        res = update_resource.apply_async(args=[self.config, res_id, 'queue1'])
        res.get()

        assert len(testipipe.calls) == 1

        operation, queue, params = testipipe.calls[0]
        assert operation == 'archived'
        assert queue == 'queue1'
        assert params.get('package_id') == None
        assert params.get('resource_id') == res_id

    @with_mock_url('?status=200&content=test&content-type=csv')
    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_package_achived_when_resource_modified(self, url, send_task):
        data_dict = self._test_resource(url)
        data_dict['url'] = 'http://example.com/foo'
        context = {'model': model, 
                   'user': 'test',
                   'ignore_auth': True,
                   'session': model.Session}
        result = get_action('resource_update')(context, data_dict)

        assert send_task.called == True

        args, kwargs = send_task.call_args
        assert args == ('archiver.update_package',)

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_ipipe_notified_dataset(self, url):
        testipipe = plugins.get_plugin('testipipe')
        testipipe.reset()

        pkg = self._test_package(url)

        # celery.send_task doesn't respect CELERY_ALWAYS_EAGER
        res = update_package.apply_async(args=[self.config, pkg['id'], 'queue1'])
        res.get()

        assert len(testipipe.calls) == 2, len(testipipe.calls)

        operation, queue, params = testipipe.calls[0]
        assert operation == 'archived'
        assert queue == 'queue1'
        assert params.get('package_id') == None
        assert params.get('resource_id') == pkg['resources'][0]['id']

        operation, queue, params = testipipe.calls[1]
        assert operation == 'package-archived'
        assert queue == 'queue1'
        assert params.get('package_id') == pkg['id']
        assert params.get('resource_id') == None

class TestDownload(BaseCase):
    '''Tests of the download method (and things it calls).

    Doesn't need a fake CKAN to get/set the status of.
    '''
    @classmethod
    def setup_class(cls):
        reset_db()
        config
        cls.fake_context = {
            'site_url': config.get('ckan.site_url_internally') or config['ckan.site_url'],
            'cache_url_root': config.get('ckanext-archiver.cache_url_root'),
        }

    def teardown(self):
        pkg = model.Package.get(u'testpkg')
        if pkg:
            model.repo.new_revision()
            pkg.purge()
            model.repo.commit_and_remove()

    def _test_resource(self, url, format=None):
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        pkg = {'name': 'testpkg', 'resources': [
            {'url': url, 'format': format or 'TXT', 'description': 'Test'}
            ]}
        pkg = get_action('package_create')(context, pkg)
        return pkg['resources'][0]

    @with_mock_url('?status=200&method=get&content=test&content-type=csv')
    def test_head_unsupported(self, url):
        # This test was more relevant when we did HEAD requests. Now servers
        # which respond badly to HEAD requests are not an issue.
        resource = self._test_resource(url)

        # HEAD request will return a 405 error, but it will persevere
        # and do a GET request which will work.
        result = download(self.fake_context, resource)
        assert result['saved_file']

    @with_mock_url('?status=200&content=test&content-type=csv')
    def test_download_file(self, url):
        resource = self._test_resource(url)

        result = download(self.fake_context, resource)

        assert result['saved_file']
        assert os.path.exists(result['saved_file'])
        _remove_archived_file(result.get('saved_file'))

        # Modify the resource and check that the resource size gets updated
        resource['url'] = url.replace('content=test', 'content=test2')
        result = download(self.fake_context, resource)
        assert_equal(result['size'], len('test2'))

        _remove_archived_file(result.get('saved_file'))

    def test_wms_1_3(self):
        with MockWmsServer(wms_version='1.3').serve() as url:
            resource = self._test_resource(url)
            result = api_request(self.fake_context, resource)

            assert result
            assert int(result['size']) > 7800, result['length']
            assert_equal(result['request_type'], 'WMS 1.3')
        _remove_archived_file(result.get('saved_file'))

    def test_wms_1_1_1(self):
        with MockWmsServer(wms_version='1.1.1').serve() as url:
            resource = self._test_resource(url)
            result = api_request(self.fake_context, resource)

            assert result
            assert int(result['size']) > 7800, result['length']
            assert_equal(result['request_type'], 'WMS 1.1.1')
        _remove_archived_file(result.get('saved_file'))

    def test_wfs(self):
        with MockWfsServer().serve() as url:
            resource = self._test_resource(url)
            result = api_request(self.fake_context, resource)

            assert result
            assert int(result['size']) > 7800, result['length']
            assert_equal(result['request_type'], 'WFS 2.0')
        _remove_archived_file(result.get('saved_file'))

    def test_wms_error(self):
        wms_error_1 = '''<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ServiceExceptionReport version="1.3.0"
  xmlns="http://www.opengis.net/ogc"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/ogc http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd">
  <ServiceException code="InvalidFormat">
Unknown service requested.
  </ServiceException>
</ServiceExceptionReport>'''
        assert_equal(response_is_an_api_error(wms_error_1), True)
        wms_error_2 = '''<ows:ExceptionReport version='1.1.0' language='en' xmlns:ows='http://www.opengis.net/ows'><ows:Exception exceptionCode='NoApplicableCode'><ows:ExceptionText>Unknown operation name.</ows:ExceptionText></ows:Exception></ows:ExceptionReport>'''
        assert_equal(response_is_an_api_error(wms_error_2), True)

def _remove_archived_file(cache_filepath):
    if cache_filepath:
        if os.path.exists(cache_filepath):
            resource_folder = os.path.split(cache_filepath)[0]
            if 'fake_resource_id' in resource_folder:
                shutil.rmtree(resource_folder)
