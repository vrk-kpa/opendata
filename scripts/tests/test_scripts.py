# -*- coding: utf-8 -*-
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import pytest
from ckan import logic

from scripts.remove_organization_members import remove_user_members_from_org


'''
You can run these tests by using the test.ini file from ckanext-ytp_main:
    $ sudo pytest --ckan-ini ../../modules/ckanext-ytp_main/test.ini test_scripts.py
'''


class MockRemoteCKAN():
    def __init__(self, action):
        self.action = action


class MockAction():
    def member_list(self, id, object_type):
        return helpers.call_action('member_list', id=id, object_type=object_type)

    def organization_member_delete(self, id, username):
        sysadmin = factories.Sysadmin()

        context = {'ignore_auth': False, 'user': sysadmin['name']}
        data_dict = {'id': id, 'username': username}

        return logic.get_action('organization_member_delete')(context=context, data_dict=data_dict)


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
class TestScripts(object):
    def test_remove_user_members_from_org(self):
        mock_api = MockRemoteCKAN(MockAction())

        user_one = factories.User(name='testuserone')
        user_two = factories.User(name='testusertwo')

        org = factories.Organization(
            name='testorg',
            users=[
                {'name': user_one['id'], 'capacity': 'editor'},
                {'name': user_two['id'], 'capacity': 'member'},
            ]
        )

        # Test with dry run
        remove_user_members_from_org(mock_api, org['id'], True)
        assert len(helpers.call_action('member_list', id=org['id'], object_type='user')) == 3

        # Test without dry run
        remove_user_members_from_org(mock_api, org['id'], False)
        assert len(helpers.call_action('member_list', id=org['id'], object_type='user')) == 0
