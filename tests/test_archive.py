import os
from datetime import datetime, timedelta
from functools import partial, wraps
from urllib import quote_plus
import urllib2

from nose.tools import raises
from mock import patch, Mock

from ckan.config.middleware import make_app
from ckan.model import Session, repo, Package, Resource, PackageExtra
from ckan.tests import BaseCase, conf_dir, url_for, CreateTestData
from ckan.lib.base import _
from ckan.lib.create_test_data import CreateTestData

from ckanext.qa.lib import log
log.create_default_logger()
from ckanext.qa.lib.db import get_resource_result, archive_result
from ckanext.qa.lib.archive import archive_resource
from tests.lib.mock_remote_server import MockEchoTestServer, MockTimeoutTestServer

TEST_PACKAGE_NAME = u'falafel'
TEST_ARCHIVE_RESULTS_FILE = 'tests/test_archive_results.db'
TEST_ARCHIVE_FOLDER = 'tests/test_archive_folder'

# make sure test archive folder exists
if not os.path.exists(TEST_ARCHIVE_FOLDER):
    os.mkdir(TEST_ARCHIVE_FOLDER)

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

def with_package_resources(*resource_urls):
    """
    Create a package with a PackageResource for each listed url. 
    Start a MockEchoTestServer to respond to the urls.
    Clean up package/extra/resource records after test function has run.
    """
    def decorator(func):
        @with_mock_url()
        @wraps(func)
        def decorated(*args, **kwargs):
            args, base_url = args[:-1], args[-1]
            Session.remove()
            rev = repo.new_revision()
            package = Package(name=TEST_PACKAGE_NAME)
            Session.add(package)
            resources = [
                Resource(
                    description=u'Resource #%d' % (ix,),
                    url=(base_url + url).decode('ascii')
                )
                for ix, url in enumerate(resource_urls)
            ]
            for r in resources:
                Session.add(r)
                package.resources.append(r)

            repo.commit()

            try:
                return func(*(args + (package,)), **kwargs)
            finally:
                for r in resources:
                    Session.delete(r)
                Session.delete(package)
                repo.commit_and_remove()
        return decorated
    return decorator
    

class TestCheckURL(BaseCase):

    @with_package_resources('?status=200')
    def test_file_url_error(self, package):
        for resource in package.resources:
            resource.url = u'file:///home/root/test.txt'
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'False', result
            assert result['message'] == 'Invalid url scheme', result

    @with_package_resources('?status=200')
    def test_bad_url_raises_BadURLError(self, package):
        for resource in package.resources:
            resource.url = u'bad://127.0.0.1'
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'False', result
            assert result['message'] == 'Invalid url scheme', result

    @with_package_resources('?status=200')
    def test_empty_url_raises_BadURLError(self, package):
        for resource in package.resources:
            resource.url = u''
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'False', result
            assert result['message'] == 'Invalid url scheme', result

    @with_package_resources('?status=503')
    def test_url_with_503_raises_TemporaryFetchError(self, package):
        for resource in package.resources:
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'False', result
            assert result['message'] == 'Service unavailable', result

    @with_package_resources('?status=404')
    def test_url_with_404_raises_PermanentFetchError(self, package):
        for resource in package.resources:
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'False', result
            assert result['message'] == 'URL unobtainable', result

    @with_package_resources('')
    def test_url_with_30x_follows_redirect(self, package):
        for resource in package.resources:
            redirect_url = resource.url + u'?status=200&content=test&content-type=text/csv'
            resource.url = resource.url + u'?status=301&location=%s' % quote_plus(redirect_url)
            archive_resource(
                TEST_ARCHIVE_FOLDER, TEST_ARCHIVE_RESULTS_FILE, resource, package.name
            )
            result = get_resource_result(TEST_ARCHIVE_RESULTS_FILE, resource.id)
            assert result['success'] == 'True', result
            assert result['message'] == 'ok', result


# class TestCheckURLScore(BaseCase):

#     @with_mock_url('?status=200;content=test;content-type=text/plain')
#     def test_url_with_content(self, url):
#         from hashlib import sha1
#         url_details = resource_details(quote_plus(url))
#         assert url_details.hash == sha1('test').hexdigest(), resource_details(url)
        
#     @with_mock_url('?status=503')
#     def test_url_with_temporary_fetch_error_not_scored(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (None, _('URL temporarily unavailable')), \
#                 resource_details(url)

#     @with_mock_url('?status=404')
#     def test_url_with_permanent_fetch_error_scores_zero(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (0, _('URL unobtainable')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=arfle/barfle-gloop')
#     def test_url_with_unknown_content_type_scores_one(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (1, _('unrecognized content type')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=text/html')
#     def test_url_pointing_to_html_page_scores_one(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (1, _('obtainable via web page')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=text/html%3B+charset=UTF-8')
#     def test_content_type_with_charset_still_recognized_as_html(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (1, _('obtainable via web page')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=text/csv')
#     def test_machine_readable_formats_score_two(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (2, _('machine readable format')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=application/json')
#     def test_open_standard_formats_score_three(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (3, _('open and standardized format')), \
#                 resource_details(url)

#     @with_mock_url('?content-type=application/rdf%2Bxml')
#     def test_ontological_formats_score_four(self, url):
#         url_details = resource_details(url)
#         assert (url_details.score, url_details.reason) == (4, _('ontologically represented')), \
#                 resource_details(url)

#     @with_mock_url('?content=TEST;content-type=application/rdf%2Bxml')
#     def test_resource_hash_and_content_length(self, url):
#         url_details = resource_details(url)
#         from hashlib import sha1
#         content_hash = sha1('TEST').hexdigest()
#         content_length = len('TEST')

#         assert url_details.hash == content_hash, url_details
#         assert url_details.content_length == content_length, url_details
