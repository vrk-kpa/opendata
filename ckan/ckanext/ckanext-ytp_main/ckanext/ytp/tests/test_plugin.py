# -*- coding: utf-8 -*-
import pytest

from ckan.tests.factories import Dataset, Group, Sysadmin, User, APIToken
from ckan.tests.helpers import call_action
from ckan.plugins import toolkit
from ckan import model
from ckan.lib.helpers import url_for

from .utils import minimal_dataset_with_one_resource_fields
from .factories import OpendataOrganization

def create_minimal_dataset():
    return {'name': 'test_dataset_1', 'title': 'test_title', 'title_translated': {'fi': "otsikko"},
            'license_id': "licence_id", 'notes_translated': {'fi': "Test notes"},
            'keywords': {'fi': ["tag1", "tag2"]},
            'collection_type': 'Open Data', 'copyright_notice_translated': {'fi': 'test_notice'},
            'maintainer': 'test_maintainer', 'maintainer_email': 'test@maintainer.org'}

@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
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
        data_dict['groups'] = [{'name': category['name']}]
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
        organization = OpendataOrganization(user=user)
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


    def test_groups_are_added(self):
        g = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })
        dataset_fields = minimal_dataset_with_one_resource_fields(Sysadmin())
        dataset_fields['groups'] = [{'name': g['name']}]
        d = Dataset(**dataset_fields)

        assert d['groups'][0]['id'] == g['id']


    def test_groups_are_updated(self):

        user = Sysadmin()

        g1 = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })

        g2 = Group(title_translated={
            "fi": "some other title in finnish",
            "sv": "some other title in swedish",
            "en": "some other title in english"
        })

        dataset_fields = minimal_dataset_with_one_resource_fields(user)

        dataset_fields['groups'] =[{'name': g1['name']}]
        d = Dataset(**dataset_fields)

        assert len(d['groups']) == 1
        assert d['groups'][0]['id'] == g1['id']

        dataset_fields['groups'] = [{'name': g2['name']}]
        dataset = call_action('package_update', context={'user': user['name']}, name=d['id'], **dataset_fields)

        assert len(dataset['groups']) == 1
        assert dataset['groups'][0]['name'] == g2['name']


    def test_groups_are_removed(self, app):
        g = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })

        user = Sysadmin()

        dataset_fields = minimal_dataset_with_one_resource_fields(user)

        dataset_fields['groups'] = [{'name': g['name']}]
        d = Dataset(**dataset_fields)

        assert len(d['groups']) == 1
        assert d['groups'][0]['id'] == g['id']
        assert d['groups'][0]['name'] == g['name']

        dataset_fields['groups'] = []
        dataset = call_action('package_update', context={'user': user['name']}, name=d['id'], **dataset_fields)
        assert len(dataset['groups']) == 0


    def test_user_can_add_datasets_to_newly_created_groups(self, app):
        user = User()
        organization = OpendataOrganization(user=user)
        dataset_fields = minimal_dataset_with_one_resource_fields(user)
        dataset = Dataset(owner_org=organization['id'], **dataset_fields)

        group = Group(title_translated={
            "fi": "some title in finnish",
            "sv": "some title in swedish",
            "en": "some title in english"
        })

        updated_dataset = call_action('package_update',
                                      context={'user': user['name'], 'ignore_auth': False},
                                      name=dataset['id'],
                                      groups=[{'name': group['name']}],
                                      **dataset_fields)
        assert len(updated_dataset['groups']) == 1

    def test_statistics_returning_correct_amounts(self):
        empty_statistics = call_action('statistics')
        assert empty_statistics == {
            'datasets': 0,
            'apisets': 0,
            'organizations': 0,
            'showcases': 0
        }

        user = User()
        OpendataOrganization(user=user)

        one_organization = call_action('statistics')
        assert one_organization == {
            'datasets': 0,
            'apisets': 0,
            'organizations': 1,
            'showcases': 0
        }

        OpendataOrganization(user=user)

        two_organizations = call_action('statistics')
        assert two_organizations == {
            'datasets': 0,
            'apisets': 0,
            'organizations': 2,
            'showcases': 0
        }

        data_dict = create_minimal_dataset()
        Dataset(**data_dict)

        added_dataset = call_action('statistics')
        assert added_dataset == {
            'datasets': 1,
            'apisets': 0,
            'organizations': 2,
            'showcases': 0
        }


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
class TestResourceStatusPlugin:
    def test_clear_sha256_and_malware_on_update(self) -> None:
        user = User()
        dataset_dict = minimal_dataset_with_one_resource_fields(user)

        dataset_dict['resources'][0]['malware'] = 'malware dummy content'
        dataset_dict['resources'][0]['sha256'] = 'sha256 dummy content'
        dataset = Dataset(**dataset_dict)
        resource = dataset['resources'][0]
        assert resource['malware'] == 'malware dummy content'
        assert resource['sha256'] == 'sha256 dummy content'

        call_action('resource_patch', id=resource['id'], position_info='modified')
        modified_resource = call_action('resource_show', id=resource['id'])

        assert modified_resource.get('malware') is None
        assert modified_resource.get('sha256') is None

    def test_keep_sha256_and_malware_when_uploading_or_setting_them(self) -> None:
        user = User()
        dataset_dict = minimal_dataset_with_one_resource_fields(user)

        dataset_dict['resources'][0]['malware'] = 'malware dummy content'
        dataset_dict['resources'][0]['sha256'] = 'sha256 dummy content'
        dataset = Dataset(**dataset_dict)
        resource = dataset['resources'][0]
        assert resource['malware'] == 'malware dummy content'
        assert resource['sha256'] == 'sha256 dummy content'

        context = {'upload_in_progress': True}
        call_action('resource_patch', id=resource['id'], position_info='modified', context=context)
        modified_resource = call_action('resource_show', id=resource['id'])

        assert modified_resource.get('malware') == 'malware dummy content'
        assert modified_resource.get('sha256') == 'sha256 dummy content'

        context = {'set_resource_status': True}
        call_action('resource_patch', id=resource['id'], position_info='modified', context=context)
        modified_resource = call_action('resource_show', id=resource['id'])

        assert modified_resource.get('malware') == 'malware dummy content'
        assert modified_resource.get('sha256') == 'sha256 dummy content'

        call_action('resource_patch', id=resource['id'], position_info='modified')
        modified_resource = call_action('resource_show', id=resource['id'])

        assert modified_resource.get('malware') is None
        assert modified_resource.get('sha256') is None


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
class TestOrganizationHierarchy:
    def test_suborganization_is_under_parent(self):
        parent = OpendataOrganization()
        child = OpendataOrganization()

        member = model.Member(
            group=model.Group.get(child['id']),
            table_id=parent['id'], table_name='group', capacity='parent')

        model.Session.add(member)
        model.Session.commit()

        result = call_action('group_tree_section', id=parent['id'], type='organization')
        assert result['children'][0]['id'] == child['id']

    def test_tree_section_has_only_approved_organizations(self):

        parent = OpendataOrganization()
        first_child = OpendataOrganization(approval_status="approved")
        second_child = OpendataOrganization(approval_status="pending")

        member = model.Member(
            group=model.Group.get(first_child['id']),
            table_id=parent['id'], table_name='group', capacity='parent')

        model.Session.add(member)
        member = model.Member(
            group=model.Group.get(second_child['id']),
            table_id=parent['id'], table_name='group', capacity='parent')
        model.Session.add(member)
        model.Session.commit()

        result = call_action('group_tree_section', id=parent['id'], type='organization', only_approved=True)

        assert result['children'][0]['id'] == first_child['id']
        assert len(result['children']) == 1

        helper_result = toolkit.h.group_tree_section(id_=parent['id'], type_='organization', only_approved=True)

        assert helper_result['children'][0]['id'] == first_child['id']
        assert len(helper_result['children']) == 1

@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
class TestOrganizationView:
    def test_organization_create_view_renders(self, app):
        user = User()
        org_url = url_for("organization.new", locale='en')

        # Unauthenticated user cannot view organization create form
        result = app.get(org_url)
        assert result.status_code == 403

        headers = {"Authorization": APIToken(user=user['name'])["token"]}
        result = app.get(org_url, headers=headers)
        assert b"Create an Organization" in result.data

    def test_organization_edit_view_renders(self, app):
        user = User()
        org = OpendataOrganization(user=user)
        org_url = url_for("organization.edit", id=org['id'], locale='en')

        # Unauthenticated user cannot view organization edit form
        result = app.get(org_url)
        assert result.status_code == 403

        headers = {"Authorization": APIToken(user=user['name'])["token"]}
        result = app.get(org_url, headers=headers)
        assert b"Edit information" in result.data

    def test_organization_members_view_renders(self, app):
        user = User()
        org = OpendataOrganization()
        org_url = url_for("organization.members", id=org['id'], locale='en')

        # Unauthenticated user cannot view organization create form
        result = app.get(org_url)
        assert result.status_code == 403

        headers = {"Authorization": APIToken(user=user['name'])["token"]}
        result = app.get(org_url, headers=headers)
        assert user['name'].encode() in result.data

    def test_deleted_organization_showing_error_message(self, app):
        org = OpendataOrganization()

        org_url = url_for("organization.read", id=org['id'], locale='en')

        call_action('organization_delete', id=org['id'])

        result = app.get(org_url)

        assert result.status_code == 404


class TestSchema:
    @pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
    def test_collection_type_filtering(self):
        opendata_dataset = create_minimal_dataset()
        Dataset(**opendata_dataset)

        interoperability_dataset = create_minimal_dataset()
        interoperability_dataset['name'] = 'test_dataset_2'
        interoperability_dataset['collection_type'] = 'Interoperability Tools'
        Dataset(**interoperability_dataset)

        test_search_result = call_action('package_search')
        assert test_search_result['count'] == 2

        filter_opendata_results = call_action('package_search', fq='collection_type:"Open Data"')
        assert filter_opendata_results['count'] == 1

        filter_interoperability_results = call_action('package_search', fq='collection_type:"Interoperability Tools"')
        assert filter_interoperability_results['count'] == 1

    @pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index', 'with_request_context')
    def test_dcat_catalog_filtering_with_collection_type(self):
        opendata_dict = create_minimal_dataset()
        opendata_dataset = Dataset(**opendata_dict)

        interoperability_dict = create_minimal_dataset()
        interoperability_dict['name'] = 'test_dataset_2'
        interoperability_dict['title'] = 'test_title_2'
        interoperability_dict['collection_type'] = 'Interoperability Tools'
        interoperability_dataset = Dataset(**interoperability_dict)

        content = call_action('dcat_catalog_show', _format='xml')

        # Parse the contents to check it's an actual serialization
        from ckanext.dcat.processors import RDFParser
        p = RDFParser()
        p.parse(content, _format='xml')
        dcat_datasets = [d for d in p.datasets()]
        assert len(dcat_datasets) == 2

        opendata_content = call_action('dcat_catalog_show', _format='xml', fq='collection_type:"Open Data"')
        opendata_parser= RDFParser()
        opendata_parser.parse(opendata_content, _format='xml')
        opendata_datasets = [d for d in opendata_parser.datasets()]
        assert len(opendata_datasets) == 1

        opendata_result = opendata_datasets[0]
        assert opendata_result['title'] == opendata_dataset['title']

        interoperability_content = call_action('dcat_catalog_show', _format='xml',
        fq='collection_type:"Interoperability Tools"')
        interoperability_parser= RDFParser()
        interoperability_parser.parse(interoperability_content, _format='xml')
        interoperability_datasets = [d for d in interoperability_parser.datasets()]
        assert len(interoperability_datasets) == 1

        interoperability_result = interoperability_datasets[0]
        assert interoperability_result['title'] == interoperability_dataset['title']
