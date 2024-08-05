# -*- coding: utf-8 -*-
import pytest

from ckan.tests.factories import Dataset, Group, Sysadmin, User, Organization
from ckan.tests.helpers import call_action
from ckan.plugins import toolkit
from .utils import minimal_dataset_with_one_resource_fields

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
        translated_title = {'fi': 'finnish title', 'sv': 'swedish title', 'en': 'english title'}
        translated_description = {'fi': 'finnish description', 'sv': 'swedish description', 'en': 'english description'}
        category = Group(title_translated=translated_title,
                         description_translated=translated_description)

        data_dict = create_minimal_dataset()
        data_dict['categories'] = [category['name']]
        dataset = Dataset(**data_dict)

        result = call_action('package_show', id=dataset['id'])
        assert result['groups'][0]['title_translated'] == translated_title
        assert result['groups'][0]['description_translated'] == translated_description


    def test_dataset_with_highvalue_category(self):
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['highvalue'] = True
        dataset_fields['highvalue_category'] = "geospatial"
        d = Dataset(**dataset_fields)
        dataset = call_action('package_show', id=d['name'])
        assert dataset['highvalue'] == 'true'
        assert dataset['highvalue_category'] == ["geospatial"]


    def test_dataset_with_multiple_highvalue_categories(self):
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['highvalue'] = True
        dataset_fields['highvalue_category'] = ["geospatial", "mobility", "earth-observation-and-environment"]
        d = Dataset(**dataset_fields)
        dataset = call_action('package_show', id=d['name'])
        assert dataset['highvalue'] == 'true'
        assert dataset['highvalue_category'] == ["geospatial", "mobility", "earth-observation-and-environment"]


    def test_highvalue_category_is_required_when_highvalue_is_true(self):
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['highvalue'] = True

        with pytest.raises(toolkit.ValidationError):
            Dataset(**dataset_fields)


    def test_dataset_with_invalid_highvalue_category(self):
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['highvalue'] = True
        dataset_fields['highvalue_category'] = "spatial"
        with pytest.raises(toolkit.ValidationError):
            Dataset(**dataset_fields)


    def test_dataset_with_highvalue_category_as_normal_user(self):
        user = User()
        organization = Organization(user=user)
        dataset_fields = minimal_dataset_with_one_resource_fields(user)
        dataset_fields['owner_org'] = organization['id']
        d = Dataset(**dataset_fields)

        dataset_fields['highvalue'] = True
        dataset_fields['highvalue_category'] = "geospatial"

        context = {"user": user["name"], "ignore_auth": False}

        d = call_action('package_update', context=context, name=d['name'], **dataset_fields)

        dataset = call_action('package_show', id=d['name'])
        assert dataset['highvalue'] == 'true'
        assert dataset['highvalue_category'] == ["geospatial"]


    def test_search_facets_with_highvalue_category(self):
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['highvalue'] = True
        dataset_fields['highvalue_category'] = ["earth-observation-and-environment"]
        Dataset(**dataset_fields)
        data_dict = {
            "facet.field": ['vocab_highvalue_category']
        }
        results = call_action('package_search', **data_dict )
        assert results['search_facets'] == {
            "vocab_highvalue_category": {
                "items": [
                    {
                        "count": 1,
                        "display_name": "Earth observation and environment",
                        "name": "earth-observation-and-environment"
                    }
                ],
                "title": "vocab_highvalue_category"
            }
        }


    def test_categories_are_added_as_groups(app):
        g = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['categories'] = g['name']
        d = Dataset(**dataset_fields)
        dataset = call_action('package_show', id=d['name'])

        assert dataset['groups'][0]['id'] == g['id']



    def test_groups_are_removed_when_categories_are_removed(app):
        g = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())

        d = Dataset(**dataset_fields)

        dataset_fields['categories'] = g['name']
        d = call_action('package_update', name=d['id'], **dataset_fields)

        dataset_fields['categories'] = []
        dataset = call_action('package_update', name=d['id'], **dataset_fields)

        assert len(dataset['groups']) == 0

