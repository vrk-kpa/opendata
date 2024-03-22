# -*- coding: utf-8 -*-
import pytest

from ckan.tests.factories import Dataset, Group
from ckan.tests.helpers import call_action
from ckan.plugins import toolkit


def create_minimal_dataset():
    return {'name': 'test_dataset_1', 'title': 'test_title', 'title_translated': {'fi': "otsikko"},
            'license_id': "licence_id", 'notes_translated': {'fi': "Test notes"},
            'keywords': {'fi': ["tag1", "tag2"]},
            'collection_type': 'Open Data', 'copyright_notice_translated': {'fi': 'test_notice'},
            'maintainer': 'test_maintainer', 'maintainer_email': 'test@maintainer.org'}

@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestYtpDatasetPlugin():
    """ Test YtpDatsetPlugin class """


    def test_create_dataset(self):
        data_dict = create_minimal_dataset()
        Dataset(**data_dict)

        test_dataset = call_action('package_show', id='test_dataset_1')
        assert test_dataset.get('title_translated').get('fi') == 'otsikko'
        assert test_dataset.get('copyright_notice_translated').get('fi') == 'test_notice'

        test_search_result = call_action('package_search', q='test')
        assert test_search_result['results'][0]['title_translated']['fi'] == 'otsikko'


    def test_external_urls_input(self):

        data_dict = create_minimal_dataset()
        data_dict['external_urls'] = ["http://foo.com", "http://bar.com"]

        dataset = Dataset(**data_dict)
        assert dataset['external_urls'] == ["http://foo.com", "http://bar.com"]


    def test_external_urls_invalid_input(self):
        data_dict = create_minimal_dataset()
        data_dict['external_urls'] = ["first", "second"]

        with pytest.raises(toolkit.ValidationError):
            Dataset(**data_dict)


    def test_external_urls_removed(self):
        data_dict = create_minimal_dataset()
        data_dict['external_urls'] = ["http://foo.com", "http://bar.com"]

        dataset = Dataset(**data_dict)


        result = call_action('package_patch', id=dataset['id'], external_urls="")
        assert result['external_urls'] == []
        result = call_action('package_patch', id=dataset['id'], external_urls=[''])
        assert result['external_urls'] == []


    def test_categories_with_translations(self):
        category = Group(title_translated={'fi': 'finnish title', 'sv': 'swedish title', 'en': 'english title'},
                         description_translated={'fi': 'finnish description',
                                                 'sv': 'swedish description',
                                                 'en': 'english description'})

        data_dict = create_minimal_dataset()
        data_dict['categories'] = [category['name']]
        dataset = Dataset(**data_dict)

        result = call_action('package_show', id=dataset['id'])
        assert result['groups'][0]['title_translated'] == {'fi': 'finnish title', 'sv': 'swedish title', 'en': 'english title'}
        assert result['groups'][0]['description_translated'] == {'fi': 'finnish description',
                                                                 'sv': 'swedish description',
                                                                 'en': 'english description'}
