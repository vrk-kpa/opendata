import requests
import logging
import urllib
import datetime

from nose.tools import assert_equal
from ckan import model
from ckan.tests import BaseCase
from ckan.logic import get_action

import ckanext.qa.tasks
from ckanext.qa.tasks import resource_score, extension_variants
import ckanext.archiver
import ckanext.archiver.tasks
from ckanext.dgu.lib.formats import Formats
from ckanext.qa import model as qa_model
from ckanext.archiver import model as archiver_model
from ckanext.archiver.model import Archival, Status

log = logging.getLogger(__name__)

# Monkey patch get_cached_resource_filepath so that it doesn't barf when
# it can't find the file
def mock_get_cached_resource_filepath(cache_url):
    if not cache_url:
        return None
    return cache_url.replace('http://remotesite.com/', '/resources')
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

TODAY = datetime.datetime(year=2008, month=10, day=10)

class TestTask(BaseCase):

    @classmethod
    def setup_class(cls):
        archiver_model.init_tables(model.meta.engine)
        qa_model.init_tables(model.meta.engine)

    def teardown(self):
        model.repo.rebuild_db()

    def test_trigger_on_archival(cls):
        # create package
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        pkg = {'name': 'testpkg', 'license_id': 'uk-ogl', 'resources': [
            {'url': 'http://test.com/', 'format': 'CSV', 'description': 'Test'}
            ]}
        pkg = get_action('package_create')(context, pkg)
        resource_dict = pkg['resources'][0]
        res_id = resource_dict['id']
        # create record of archival
        archival = Archival.create(res_id)
        cache_filepath = __file__  # just needs to exist
        archival.cache_filepath = cache_filepath
        archival.updated = TODAY
        model.Session.add(archival)
        model.Session.commit()
        # TODO show that QA hasn't run yet

        # create a send_data from ckanext-archiver, that gets picked up by
        # ckanext-qa to put a task on the queue
        ckanext.archiver.tasks.notify(resource_dict, cache_filepath)
        # this is useful on its own (without any asserts) because it checks
        # there are no exceptions when running it

        # TODO run celery and check it actually ran...


class TestResourceScore(BaseCase):

    @classmethod
    def setup_class(cls):
        archiver_model.init_tables(model.meta.engine)
        qa_model.init_tables(model.meta.engine)
        cls.fake_resource = {
            'id': u'fake_resource_id',
            'url': 'http://remotesite.com/filename.csv',
            'cache_url': 'http://remotesite.com/resources/filename.csv',
            'cache_filepath': __file__,  # must exist
            'package': u'fake_package_id',
            'is_open': True,
            'position': 2,
        }

    def teardown(self):
        model.repo.rebuild_db()

    def _test_resource(self, url='anything', format='TXT', archived=True, cached=True, license_id='uk-ogl'):
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        pkg = {'name': 'testpkg', 'license_id': license_id, 'resources': [
            {'url': url, 'format': format, 'description': 'Test'}
            ]}
        pkg = get_action('package_create')(context, pkg)
        res_id = pkg['resources'][0]['id']
        if archived:
            archival = Archival.create(res_id)
            archival.cache_filepath = __file__ if cached else None  # just needs to exist
            archival.updated = TODAY
            model.Session.add(archival)
            model.Session.commit()
        return model.Resource.get(res_id)

    @classmethod
    def _set_task_status(cls, task_type, task_status_str):
        url = '%s/set_task_status/%s/%s' % (cls.fake_ckan_url,
                                            task_type,
                                            urllib.quote(task_status_str))
        res = requests.get(url)
        assert res.status_code == 200

    def test_by_sniff_csv(self):
        set_sniffed_format('CSV')
        result = resource_score(self._test_resource(), log)
        assert result['openness_score'] == 3, result
        assert 'Content of file appeared to be format "CSV"' in result['openness_score_reason'], result
        assert result['format'] == 'CSV', result
        assert result['archival_timestamp'] == TODAY, result

    def test_not_archived(self):
        result = resource_score(self._test_resource(archived=False, cached=False, format=None), log)
        # falls back on previous QA data detailing failed attempts
        assert result['openness_score'] == 1, result
        assert result['format'] == None, result
        assert result['archival_timestamp'] == None, result
        assert 'This file had not been downloaded at the time of scoring it.' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL.' in result['openness_score_reason'], result
        assert 'Format field is blank.' in result['openness_score_reason'], result
        assert 'Could not understand the file format, therefore score is 1.' in result['openness_score_reason'], result

    def test_archiver_ran_but_not_cached(self):
        result = resource_score(self._test_resource(cached=False, format=None), log)
        # falls back on previous QA data detailing failed attempts
        assert result['openness_score'] == 1, result
        assert result['format'] == None, result
        assert result['archival_timestamp'] == TODAY, result
        assert 'This file had not been downloaded at the time of scoring it.' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL.' in result['openness_score_reason'], result
        assert 'Format field is blank.' in result['openness_score_reason'], result
        assert 'Could not understand the file format, therefore score is 1.' in result['openness_score_reason'], result

    def test_by_extension(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource('http://site.com/filename.xls'), log)
        assert result['openness_score'] == 2, result
        assert result['archival_timestamp'] == TODAY, result
        assert_equal(result['format'], 'XLS')
        assert 'not recognized from its contents' in result['openness_score_reason'], result
        assert 'extension "xls" relates to format "XLS"' in result['openness_score_reason'], result

    def test_extension_not_recognized(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource('http://site.com/filename.zar'), log)
        assert result['openness_score'] == 1, result
        assert 'not recognized from its contents' in result['openness_score_reason'], result
        assert 'URL extension "zar" is an unknown format' in result['openness_score_reason'], result

    def test_by_format_field(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource(format='XLS'), log)
        assert result['openness_score'] == 2, result
        assert_equal(result['format'], 'XLS')
        assert 'not recognized from its contents' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL' in result['openness_score_reason'], result
        assert 'Format field "XLS"' in result['openness_score_reason'], result

    def test_by_format_field_excel(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource(format='Excel'), log)
        assert_equal(result['format'], 'XLS')

    def test_format_field_not_recognized(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource(format='ZAR'), log)
        assert result['openness_score'] == 1, result
        assert 'not recognized from its contents' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL' in result['openness_score_reason'], result
        assert 'Format field "ZAR" does not correspond to a known format' in result['openness_score_reason'], result

    def test_no_format_clues(self):
        set_sniffed_format(None)
        result = resource_score(self._test_resource(format=None), log)
        assert result['openness_score'] == 1, result
        assert 'not recognized from its contents' in result['openness_score_reason'], result
        assert 'Could not determine a file extension in the URL' in result['openness_score_reason'], result
        assert 'Format field is blank' in result['openness_score_reason'], result

    def test_available_but_not_open(self):
        set_sniffed_format('CSV')
        result = resource_score(self._test_resource(license_id=None), log)
        assert result['openness_score'] == 0, result
        assert_equal(result['format'], 'CSV')
        assert 'License not open' in result['openness_score_reason'], result

    def test_not_available_and_not_open(self):
        res = self._test_resource(license_id=None, format=None, cached=False)
        archival = Archival.get_for_resource(res.id)
        archival.status_id = Status.by_text('Download error')
        archival.reason = 'Server returned 500 error'
        archival.last_success = None
        archival.first_failure = datetime.datetime(year=2008, month=10, day=1, hour=6, minute=30)
        archival.failure_count = 16
        archival.is_broken = True
        model.Session.commit()
        result = resource_score(res, log)
        assert result['openness_score'] == 0, result
        assert_equal(result['format'], None)
        # in preference it should report that it is not available
        assert_equal(result['openness_score_reason'], 'File could not be downloaded. Reason: Download error. Error details: Server returned 500 error. Attempted on 10/10/2008. Tried 16 times since 01/10/2008. This URL has not worked in the history of this tool.')

    def test_not_available_any_more(self):
        # A cache of the data still exists from the previous run, but this
        # time, the archiver found the file gave a 404.
        # The record of the previous (successful) run of QA.
        res = self._test_resource(license_id=None, format=None)
        qa = qa_model.QA.create(res.id)
        qa.format = 'CSV'
        model.Session.add(qa)
        model.Session.commit()
        # cache still exists from the previous run, but this time, the archiver
        # found the file gave a 404.
        archival = Archival.get_for_resource(res.id)
        archival.cache_filepath = __file__
        archival.status_id = Status.by_text('Download error')
        archival.reason = 'Server returned 404 error'
        archival.last_success = datetime.datetime(year=2008, month=10, day=1)
        archival.first_failure = datetime.datetime(year=2008, month=10, day=2)
        archival.failure_count = 1
        archival.is_broken = True
        result = resource_score(res, log)
        assert result['openness_score'] == 0, result
        assert_equal(result['format'], 'CSV')
        # in preference it should report that it is not available
        assert_equal(result['openness_score_reason'], 'File could not be downloaded. Reason: Download error. Error details: Server returned 404 error. Attempted on 10/10/2008. This URL worked the previous time: 01/10/2008.')


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
