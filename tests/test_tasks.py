import os
import subprocess
import time
import requests
import json
import logging
import datetime
from functools import wraps

from nose.tools import raises, assert_equal
from ckan import model
from ckan.tests import BaseCase

import ckanext.qa.tasks
from ckanext.qa.tasks import resource_score, update, extension_variants
from ckanext.dgu.lib.formats import Formats

log = logging.getLogger(__name__)

# Monkey patch get_cached_resource_filepath so that it doesn't barf when
# it can't find the file
def mock_get_cached_resource_filepath(data):
    if not data.get('cache_url'):
        return None
    return data.get('cache_url').replace('http://remotesite.com/', '/resources')
ckanext.qa.tasks.get_cached_resource_filepath = mock_get_cached_resource_filepath

# Monkey patch sniff_file_format. This isolates the testing of tasks from
# actual sniffing
sniffed_format = None
def mock_sniff_file_format(filepath, log):
    return sniffed_format
ckanext.qa.tasks.sniff_file_format = mock_sniff_file_format
def set_sniffed_format(format_display_name):
    global sniffed_format
    if format_display_name:
        sniffed_format = Formats.by_display_name()[format_display_name]
    else:
        sniffed_format = None
    
class TestResourceScore(BaseCase):

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
            'url': 'http://remotesite.com/filename.csv',
            'cache_url': '/resources/filename.csv',
            'package': u'fake_package_id',
            'is_open': True,
            'position': 2,
        }

    @classmethod
    def teardown_class(cls):
        cls.fake_ckan.kill()

    def test_by_sniff_csv(self):
        set_sniffed_format('CSV')
        data = self.fake_resource
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 3, result
        assert 'Content of file appeared to be format "CSV"' in result['openness_score_reason'], result

    def test_by_sniff_xls(self):
        set_sniffed_format('XLS')
        data = self.fake_resource
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 2, result
        assert 'Content of file appeared to be format "XLS"' in result['openness_score_reason'], result

    def test_not_cached(self):
        data = self.fake_resource
        data['cache_url'] = None
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 3, result
        assert 'Cached copy of the data not currently available' in result['openness_score_reason'], result
        # recognised by extension

    def test_by_extension(self):
        set_sniffed_format(None)
        data = self.fake_resource
        data['url'] = data['url'].replace('csv', 'xls')
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 2, result
        assert 'not recognised from its contents' in result['openness_score_reason'], result
        assert 'extension "xls" relates to format "XLS"' in result['openness_score_reason'], result

    def test_by_format_field(self):
        set_sniffed_format(None)
        data = self.fake_resource
        data['url'] = data['url'].replace('.csv', '')
        data['format'] = 'CSV'
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 3, result
        assert 'not recognised from its contents' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL' in result['openness_score_reason'], result
        assert 'Format field "CSV"' in result['openness_score_reason'], result

    def test_no_format_clues(self):
        set_sniffed_format(None)
        data = self.fake_resource
        data['url'] = data['url'].replace('.csv', '')
        data['format'] = ''
        result = resource_score(self.fake_context, data, log)
        assert result['openness_score'] == 0, result
        assert 'not recognised from its contents' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL' in result['openness_score_reason'], result
        assert 'Format field is blank' in result['openness_score_reason'], result

    # if it downloads but we don't recognise the format it should get 1 star,
    # but that hasn't been implemented yet.

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
        score_last_success = False

        for d in task_data:
            assert d['entity_id'] == 'fake_resource_id', d
            assert d['entity_type'] == 'resource', d
            assert d['task_type'] == 'qa', d

            if d['key'] == 'openness_score':
                score = True
                assert d['value'] == 3, d
            elif d['key'] == 'openness_score_reason':
                score_reason = True
                assert d['value'] == 'Request succeeded. Content-Type header "text/csv".', d
            elif d['key'] == 'openness_score_failure_count':
                score_failure_count = True
                assert d['value'] == 0, d
            elif d['key'] == 'openness_score_last_success':
                score_last_success = True
                todays_date = datetime.datetime.now().isoformat()[:10]
                assert d['value'].startswith(todays_date), d

        assert score
        assert score_reason
        assert score_failure_count
        assert score_last_success

class TestExtensionVariants:
    def test_0_normal(self):
        assert_equal(extension_variants('http://dept.gov.uk/coins-data-1996.csv'),
                     ['csv'])

    def test_1_multiple(self):
        assert_equal(extension_variants('http://dept.gov.uk/coins.data.1996.csv.zip'),
                     ['csv.zip', 'zip'])
            
    def test_2_parameter(self):
        assert_equal(extension_variants('http://dept.gov.uk/coins-data-1996.csv?callback=1'),
                     ['csv'])

    def test_3_none(self):
        assert_equal(extension_variants('http://dept.gov.uk/coins-data-1996'),
                     [])
