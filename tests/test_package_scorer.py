from datetime import datetime, timedelta
from functools import partial, wraps
from urllib import quote_plus
import urllib2

from nose.tools import raises
from mock import patch, Mock

from ckan.config.middleware import make_app
from ckan.model import Package, PackageResource, PackageExtra
from ckan.tests import BaseCase, conf_dir, url_for, CreateTestData
from ckan.lib.base import _
from ckan.lib.create_test_data import CreateTestData
from ckanext.qa.lib.package_scorer import \
        PKGEXTRA, response_for_url, url_score, update_package_score, \
        next_check_time, retry_interval, \
        BadURLError, TemporaryFetchError, PermanentFetchError
from ckan.model import Session, repo

from tests.lib.mock_remote_server import MockEchoTestServer, MockTimeoutTestServer

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
            package = Package(name=u'falafel')
            Session.add(package)
            resources = [
                PackageResource(
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
                
                package.extras = {}
                Session.flush()
                Session.delete(package)
                repo.commit_and_remove()
        return decorated
    return decorator
    

class TestCheckURL(BaseCase):

    @raises(BadURLError)
    def test_file_url_raises_BadURLError(self):
        response_for_url('file:///etc/passwd')

    @raises(BadURLError)
    def test_bad_url_raises_BadURLError(self):
        response_for_url('bad://127.0.0.1/')

    @raises(BadURLError)
    def test_empty_url_raises_BadURLError(self):
        response_for_url('')

    @raises(TemporaryFetchError)
    @with_mock_url('/?status=503')
    def test_url_with_503_raises_TemporaryFetchError(self, url):
        response_for_url(url)

    @raises(PermanentFetchError)
    @with_mock_url('/?status=404')
    def test_url_with_404_raises_PermanentFetchError(self, url):
        response_for_url(url)

    def test_url_with_30x_follows_redirect(self):
        with MockEchoTestServer().serve() as serveraddr:
            redirecturl = '%s/?status=200;content=test' % (serveraddr,)
            response = response_for_url('%s/?status=301;location=%s' % (serveraddr, quote_plus(redirecturl)))
            assert response.read() == 'test'


    @raises(TemporaryFetchError)
    def test_timeout_raises_temporary_fetch_error(self):
        with patch('ckanext.qa.lib.package_scorer.url_timeout', 0.5):
            def test():
                with MockTimeoutTestServer(2).serve() as serveraddr:
                    response = response_for_url(serveraddr)
            test()

class TestCheckURLScore(BaseCase):

    @with_mock_url('?status=503')
    def test_url_with_temporary_fetch_error_not_scored(self, url):
        assert url_score(url) == (None, _('URL temporarily unavailable')), \
                url_score(url)

    @with_mock_url('?status=404')
    def test_url_with_permanent_fetch_error_scores_zero(self, url):
        assert url_score(url) == (0, _('URL unobtainable')), \
                url_score(url)

    @with_mock_url('?content-type=arfle/barfle-gloop')
    def test_url_with_unknown_content_type_scores_one(self, url):
        assert url_score(url) == (1, _('unrecognized content type')), \
                url_score(url)

    @with_mock_url('?content-type=text/html')
    def test_url_pointing_to_html_page_scores_one(self, url):
        assert url_score(url) == (1, _('obtainable via web page')), \
                url_score(url)

    @with_mock_url('?content-type=text/html%3B+charset=UTF-8')
    def test_content_type_with_charset_still_recognized_as_html(self, url):
        assert url_score(url) == (1, _('obtainable via web page')), \
                url_score(url)

    @with_mock_url('?content-type=text/csv')
    def test_machine_readable_formats_score_two(self, url):
        assert url_score(url) == (2, _('machine readable format')), \
                url_score(url)

    @with_mock_url('?content-type=application/json')
    def test_open_standard_formats_score_three(self, url):
        assert url_score(url) == (3, _('open and standardized format')), \
                url_score(url)

    @with_mock_url('?content-type=application/rdf%2Bxml')
    def test_ontological_formats_score_four(self, url):
        assert url_score(url) == (4, _('ontologically represented')), \
                url_score(url)

class TestCheckPackageScore(BaseCase):

    @with_package_resources('?status=503')
    def test_temporary_failure_increments_failure_count(self, package):

        update_package_score(package)
        assert package.extras[PKGEXTRA.openness_score_failure_count] == 1, \
            package.extras[PKGEXTRA.openness_score_failure_count]

        update_package_score(package, force=True)
        assert package.extras[PKGEXTRA.openness_score_failure_count] == 2, \
            package.extras[PKGEXTRA.openness_score_failure_count]

    @with_package_resources('?status=200')
    def test_update_package_resource_creates_all_extra_records(self, package):
        update_package_score(package)
        for key in PKGEXTRA:
            assert key in package.extras, (key, package.extras)

    @with_package_resources('?status=200')
    def test_update_package_doesnt_update_overridden_package(self, package):
        update_package_score(package)
        package.extras[PKGEXTRA.openness_score_override] = 5
        update_package_score(package)
        assert package.extras[PKGEXTRA.openness_score_override] == 5

    @with_package_resources('?status=503')
    def test_repeated_temporary_failures_give_permanent_failure(self, package):
        for ix in range(5):
            update_package_score(package, force=True)
            assert package.extras[PKGEXTRA.openness_score] == None

        update_package_score(package, force=True)
        assert package.extras[PKGEXTRA.openness_score] == 0

    @with_package_resources('')
    def test_repeated_temporary_failure_doesnt_cause_previous_score_to_be_reset(self, package):
        baseurl = package.resources[0].url

        package.resources[0].url = baseurl + '?status=200;content-type=application/rdf%2Bxml'
        update_package_score(package)
        assert package.extras[PKGEXTRA.openness_score] == 4.0, package.extras

        package.resources[0].url = baseurl + '?status=503'
        update_package_score(package, force=True)
        assert package.extras[PKGEXTRA.openness_score] == 4.0, package.extras

    @with_package_resources('?status=503')
    def test_package_retry_interval_backs_off(self, package):

        base_time = datetime(1970, 1, 1, 0, 0, 0)
        mock_datetime = Mock()
        mock_datetime.now.return_value = base_time

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            update_package_score(package)
        assert next_check_time(package) == base_time + retry_interval

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            update_package_score(package, force=True)
        assert next_check_time(package) == base_time + 2 * retry_interval

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            update_package_score(package, force=True)
        assert next_check_time(package) == base_time + 4 * retry_interval

    @with_package_resources('?status=200')
    def test_package_retry_interval_used_on_successful_scoring(self, package):

        base_time = datetime(1970, 1, 1, 0, 0, 0)
        mock_datetime = Mock()
        mock_datetime.now.return_value = base_time

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            update_package_score(package)
        assert next_check_time(package) == base_time + retry_interval, next_check_time(package)
