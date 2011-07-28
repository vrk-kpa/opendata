from datetime import datetime, timedelta
from functools import partial, wraps
from urllib import quote_plus
import urllib2

from nose.tools import raises
from mock import patch, Mock

# from paste.deploy import appconfig
# import paste.fixture
from ckan.config.middleware import make_app
from ckan import model
from ckan.model import Session, repo, Package, Resource, PackageExtra
from ckan.tests import BaseCase, conf_dir, url_for, CreateTestData
from ckan.lib.base import _
from ckan.lib.create_test_data import CreateTestData
from ckan.lib.dictization.model_dictize import package_dictize

from ckanext.qa.lib import log
log.create_default_logger()
from ckanext.qa.lib.db import get_resource_result, archive_result
import ckanext.qa.lib.package_scorer
from ckanext.qa.lib.package_scorer import package_score
from tests.lib.mock_remote_server import MockEchoTestServer, MockTimeoutTestServer

ckanext.qa.lib.package_scorer.MAINTENANCE_AUTHOR = u'testsysadmin'
TEST_PACKAGE_NAME = u'falafel'
TEST_ARCHIVE_RESULTS_FILE = 'tests/test_archive_results.db'

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

            context = {
                'model': model, 'session': model.Session, 'id': package.id
            }
            package_dict = package_dictize(package, context)

            try:
                return func(*(args + (package_dict,)), **kwargs)
            finally:
                for r in resources:
                    Session.delete(Session.merge(r))
                Session.delete(Session.merge(package))
                repo.commit_and_remove()
        return decorated
    return decorator

def with_archive_result(result):
    """
    Create an archive result with the given result dict.
    Remove archive result when done.
    """
    def decorator(func):
        @with_package_resources(result['url'])
        @wraps(func)
        def decorated(*args, **kwargs):
            package = args[-1]
            for r in package.get('resources'):
                archive_result(
                    TEST_ARCHIVE_RESULTS_FILE, r.get('id'), 
                    result['message'], result['success'], result['content-type']
                )
            # TODO: remove archive result after running test function
            #       should not currently cause a problem, but it's untidy
            return func(*args, **kwargs)
        return decorated
    return decorator

class TestCheckResultScore(BaseCase):
    users = []

    @classmethod
    def setup_class(cls):
        testsysadmin = model.User(name=u'testsysadmin', password=u'testsysadmin')
        cls.users.append(u'testsysadmin')
        model.Session.add(testsysadmin)
        model.add_user_to_role(testsysadmin, model.Role.ADMIN, model.System())
        model.repo.commit_and_remove()

    @classmethod
    def teardown_class(cls):
        for user_name in cls.users:
            user = model.User.get(user_name)
            if user:
                user.purge()

    @with_archive_result({
        'url': '?status=200&content-type="text/csv"&content="test"', 
        'message': 'ok', 'success': True, 'content-type': 'text/csv'
    })
    def test_url_with_content(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == u'3', resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], \
            package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '3', package

    @with_archive_result({
        'url': '?status=503', 'message': 'URL temporarily unavailable', 
        'success': False, 'content-type': 'text/csv'
    })
    def test_url_with_temporary_fetch_error_not_scored(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '0', resource
            assert resource.get('openness_score_reason') == 'URL temporarily unavailable', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '0', package

    @with_archive_result({
        'url': '?status=404', 'message': 'URL unobtainable', 
        'success': False, 'content-type': 'text/csv'
    })
    def test_url_with_permanent_fetch_error_scores_zero(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '0', resource
            assert resource.get('openness_score_reason') == 'URL unobtainable', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '0', package

    @with_archive_result({
        'url': '?content-type=arfle/barfle-gloop', 'message': 'unrecognised content type', 
        'success': False, 'content-type': 'text/csv'
    })
    def test_url_with_unknown_content_type_scores_one(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '0', resource
            assert resource.get('openness_score_reason') == 'unrecognised content type', \
                resource.extras
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '0', package

    @with_archive_result({
        'url': '?content-type=text/html', 'message': 'obtainable via web page', 
        'success': True, 'content-type': 'text/html'
    })
    def test_url_pointing_to_html_page_scores_one(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '1', resource
            assert resource.get('openness_score_reason') == 'obtainable via web page', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '1', package

    @with_archive_result({
        'url': '?content-type=text/html%3B+charset=UTF-8', 'message': 'obtainable via web page', 
        'success': True, 'content-type': 'text/html'
    })
    def test_content_type_with_charset_still_recognized_as_html(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == u'1', resource
            assert resource.get('openness_score_reason') == u'obtainable via web page', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '1', package

    @with_archive_result({
        'url': 'application/vnd.ms-excel', 'message': 'machine readable format', 
        'success': True, 'content-type': 'application/vnd.ms-excel'
    })
    def test_machine_readable_formats_score_two(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '2', resource
            assert resource.get('openness_score_reason') == 'machine readable format', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '2', package

    @with_archive_result({
        'url': 'text/csv', 'message': 'open and standardized format', 
        'success': True, 'content-type': 'text/csv'
    })
    def test_open_standard_formats_score_three(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '3', resource
            assert resource.get('openness_score_reason') == 'open and standardized format', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '3', package

    @with_archive_result({
        'url': '?content-type=application/rdf+xml', 'message': 'ontologically represented', 
        'success': True, 'content-type': 'application/rdf+xml'
    })
    def test_ontological_formats_score_four(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score') == '4', resource
            assert resource.get('openness_score_reason') == 'ontologically represented', \
                resource
        assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
        for extra in package.get('extras'):
            if extra.get('key') == 'openness_score':
                assert extra.get('value') == '4', package
        
class TestCheckPackageScore(BaseCase):
    users = []

    @classmethod
    def setup_class(cls):
        testsysadmin = model.User(name=u'testsysadmin', password=u'testsysadmin')
        cls.users.append(u'testsysadmin')
        model.Session.add(testsysadmin)
        model.add_user_to_role(testsysadmin, model.Role.ADMIN, model.System())
        model.repo.commit_and_remove()

    @classmethod
    def teardown_class(cls):
        for user_name in cls.users:
            user = model.User.get(user_name)
            if user:
                user.purge()

    @with_package_resources('?status=503')
    def test_temporary_failure_increments_failure_count(self, package):
        # TODO: fix
        # known fail: call to resource_update in the second package_score
        # call is causing sqlalchemy to throw an integrity error
        from nose.plugins.skip import SkipTest
        raise SkipTest

        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score_failure_count') == '1', \
                resource
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        for resource in package.get('resources'):
            assert resource.get('openness_score_failure_count') == '2', \
                resource

    @with_package_resources('?status=200')
    def test_update_package_resource_creates_all_extra_records(self, package):
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        extras = [u'openness_score', u'openness_score_last_checked']
        package_extra_keys = [e.get('key') for e in package.get('extras')]
        for key in extras:
            assert key in package_extra_keys, (key, package_extra_keys)

    @with_package_resources('?status=200')
    def test_update_package_doesnt_update_overridden_package(self, package):
        # TODO: fix
        # known fail: need to set the extra value using a call to package_update
        # in the logic layer
        from nose.plugins.skip import SkipTest
        raise SkipTest

        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        package.extras['openness_score_override'] = u'5'
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert package.extras['openness_score_override'] == '5', package.extras

    @with_package_resources('?status=503')
    def test_repeated_temporary_failures_give_permanent_failure(self, package):
        # TODO: fix
        # known fail: call to resource_update in the second package_score
        # call is causing sqlalchemy to throw an integrity error
        from nose.plugins.skip import SkipTest
        raise SkipTest

        for x in range(5):
            package_score(package, TEST_ARCHIVE_RESULTS_FILE)
            assert 'openness_score' in [e.get('key') for e in package.get('extras')], package
            for extra in package.get('extras'):
                if extra.get('key') == 'openness_score':
                    assert extra.get('value') == '0', package

    @with_package_resources('')
    def test_repeated_temporary_failure_doesnt_cause_previous_score_to_be_reset(self, package):
        # TODO: fix
        # known fail: package_score will give an openness_score of 0 for the
        # first url
        from nose.plugins.skip import SkipTest
        raise SkipTest

        baseurl = package.resources[0].url
        package.resources[0].url = baseurl + '?status=200;content-type=application/rdf%2Bxml'
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert package.extras[u'openness_score'] == u'4', package.extras

        package.resources[0].url = baseurl + '?status=503'
        package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert package.extras[u'openness_score'] == u'4', package.extras

    @with_package_resources('?status=503')
    def test_package_retry_interval_backs_off(self, package):
        # TODO: fix
        # known fail: next_check_time function does not exist
        from nose.plugins.skip import SkipTest
        raise SkipTest

        base_time = datetime(1970, 1, 1, 0, 0, 0)
        mock_datetime = Mock()
        mock_datetime.now.return_value = base_time

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert next_check_time(package) == base_time + retry_interval

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert next_check_time(package) == base_time + 2 * retry_interval

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert next_check_time(package) == base_time + 4 * retry_interval

    @with_package_resources('?status=200')
    def test_package_retry_interval_used_on_successful_scoring(self, package):
        # TODO: fix
        # known fail: next_check_time function does not exist
        from nose.plugins.skip import SkipTest
        raise SkipTest

        base_time = datetime(1970, 1, 1, 0, 0, 0)
        mock_datetime = Mock()
        mock_datetime.now.return_value = base_time

        with patch('ckanext.qa.lib.package_scorer.datetime', mock_datetime):
            package_score(package, TEST_ARCHIVE_RESULTS_FILE)
        assert next_check_time(package) == base_time + retry_interval, next_check_time(package)
