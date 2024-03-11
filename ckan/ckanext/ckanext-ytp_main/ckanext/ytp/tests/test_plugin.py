# -*- coding: utf-8 -*-
import pytest

from ckan.tests.factories import Dataset
from ckan.tests.helpers import call_action

@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestYtpDatasetPlugin():
    """ Test YtpDatsetPlugin class """


    def test_create_dataset(self):
        data_dict = {'name': 'test_dataset_1', 'title': 'test_title', 'title_translated': {'fi': "otsikko"},
                     'license_id': "licence_id", 'notes_translated': {'fi': "Test notes"},
                     'keywords': {'fi': ["tag1", "tag2"]},
                     'collection_type': 'Open Data', 'copyright_notice_translated': {'fi': 'test_notice'},
                     'maintainer': 'test_maintainer', 'maintainer_email': 'test@maintainer.org'}


        Dataset(**data_dict)

        test_dataset = call_action('package_show', id='test_dataset_1')
        assert test_dataset.get('title_translated').get('fi') == 'otsikko'
        assert test_dataset.get('copyright_notice_translated').get('fi') == 'test_notice'

        test_search_result = call_action('package_search', q='test')
        assert test_search_result['results'][0]['title_translated']['fi'] == 'otsikko'
