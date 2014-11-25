import os
import subprocess
import time
import requests
import json
from functools import wraps
from mock import patch, Mock
from nose.tools import raises
from ckan import model
from ckan.tests import BaseCase

from ckanext.qa.tasks import resource_score, update
from mock_remote_server import MockEchoTestServer, MockTimeoutTestServer

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


class TestResultScore(BaseCase):

    @classmethod
    def setup_class(cls):
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
            'apikey': u'fake_api_key'
        }
        cls.fake_resource = {
            'id': u'fake_resource_id',
            'url': cls.fake_ckan_url,
            'package': u'fake_package_id',
            'is_open': True,
            'position': 2,
        }

    @classmethod
    def teardown_class(cls):
        cls.fake_ckan.kill()

    @with_mock_url('?status=200&content-type=text%2Fcsv&content=test')
    def test_url_with_content(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 3, result

    @with_mock_url('?status=503')
    def test_url_with_temporary_fetch_error_not_scored(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 0, result
        assert result['openness_score_reason'] == 'Service unavailable' or \
            result['openness_score_reason'] == 'Server returned error: Service unavailable', result

    @with_mock_url('?status=404')
    def test_url_with_permanent_fetch_error_scores_zero(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 0, result
        assert result['openness_score_reason'] == 'URL unobtainable' or \
            result['openness_score_reason'] == 'URL unobtainable: Server returned HTTP 404', result

    @with_mock_url('?content-type=arfle%2Fbarfle-gloop')
    def test_url_with_unknown_content_type_scores_one(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 0, result
        assert result['openness_score_reason'] == 'unrecognised content type', result

    @with_mock_url('?content-type=text%2Fplain')
    def test_url_pointing_to_html_page_scores_one(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 1, result
        assert result['openness_score_reason'] == 'obtainable via web page', result

    @with_mock_url('?content-type=text%2Fplain%3B+charset=UTF-8')
    def test_content_type_with_charset_still_recognized(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 1, result
        assert result['openness_score_reason'] == 'obtainable via web page', result

    @with_mock_url('?content-type=application%2Fvnd.ms-excel')
    def test_machine_readable_formats_score_two(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 2, result
        assert result['openness_score_reason'] == 'machine readable format', result

    @with_mock_url('?content-type=text%2Fcsv')
    def test_open_standard_formats_score_three(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 3, result
        assert result['openness_score_reason'] == 'open and standardized format', result

    @with_mock_url('?content-type=application%2Frdf%2Bxml')
    def test_ontological_formats_score_four(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score'] == 4, result
        assert result['openness_score_reason'] == 'ontologically represented', result

    @with_mock_url('?status=503')
    def test_temporary_failure_increments_failure_count(self, url):
        data = self.fake_resource
        data['url'] = url
        result = resource_score(self.fake_context, data)
        assert result['openness_score_failure_count'] == 1, result
        

class TestTask(BaseCase):
    @classmethod
    def setup_class(cls):
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
            'apikey': u'fake_api_key'
        }
        cls.fake_resource = {
            'id': u'fake_resource_id',
            'url': cls.fake_ckan_url,
            'package': u'fake_package_id',
            'is_open': True,
            'position': 2,
        }

    @classmethod
    def teardown_class(cls):
        cls.fake_ckan.kill()

    @with_mock_url('?status=200&content=test&content-type=text%2Fcsv')
    def test_task_updates_task_status_table(self, url):
        data = self.fake_resource
        data['url'] = url
        context = json.dumps(self.fake_context)
        data = json.dumps(data)
        result = json.loads(update(context, data))

        response = requests.get(self.fake_ckan_url + '/last_request')
        headers = json.loads(response.content)['headers']
        
        assert headers['Content-Type'] == 'application/json', headers
        assert headers['Authorization'] == 'fake_api_key', headers

        task_data = json.loads(response.content)['data']['data']

        score = False
        score_reason = False
        score_failure_count = False

        for d in task_data:
            assert d['entity_id'] == 'fake_resource_id', d
            assert d['entity_type'] == 'resource', d
            assert d['task_type'] == 'qa', d

            if d['key'] == 'openness_score':
                score = True
                assert d['value'] == 3, d
            elif d['key'] == 'openness_score_reason':
                score_reason = True
                assert d['value'] == 'open and standardized format', d
            elif d['key'] == 'openness_score_failure_count':
                score_failure_count = True
                assert d['value'] == 0, d

        assert score
        assert score_reason
        assert score_failure_count

