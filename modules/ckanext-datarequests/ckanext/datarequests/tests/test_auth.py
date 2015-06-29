# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of CKAN Data Requests Extension.

# CKAN Data Requests Extension is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# CKAN Data Requests Extension is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with CKAN Data Requests Extension. If not, see <http://www.gnu.org/licenses/>.


import ckanext.datarequests.constants as constants
import ckanext.datarequests.auth as auth
import unittest

from mock import MagicMock
from nose_parameterized import parameterized

# Needed for the test
context = {
    'user': 'example_usr',
    'auth_user_obj': MagicMock(),
    'model': MagicMock(),
    'session': MagicMock()
}

request_data_dr = {
    'title': 'title',
    'description': 'description',
    'organization_id': 'organization'
}

request_data_comment = {
    'id': 'title',
    'datarequest_id': 'example_uuid_v4',
    'comment': 'This is an example comment'
}


class AuthTest(unittest.TestCase):

    def setUp(self):
        self._tk = auth.tk
        auth.tk = MagicMock()

    def tearDown(self):
        auth.tk = self._tk

    @parameterized.expand([
        # Data Requests
        (auth.datarequest_create, None,    None),
        (auth.datarequest_create, context, None),
        (auth.datarequest_create, None,    request_data_dr),
        (auth.datarequest_create, context, request_data_dr),
        (auth.datarequest_show,   None,    None),
        (auth.datarequest_show,   context, None),
        (auth.datarequest_show,   None,    request_data_dr),
        (auth.datarequest_show,   context, request_data_dr),
        (auth.datarequest_index,  None,    None),
        (auth.datarequest_index,  context, None),
        (auth.datarequest_index,  None,    request_data_dr),
        (auth.datarequest_index,  context, request_data_dr),
        # Comments
        (auth.datarequest_comment,        None,    None),
        (auth.datarequest_comment,        context, None),
        (auth.datarequest_comment,        None,    request_data_comment),
        (auth.datarequest_comment,        context, request_data_comment),
        (auth.datarequest_comment_show,   None,    None),
        (auth.datarequest_comment_show,   context, None),
        (auth.datarequest_comment_show,   None,    request_data_comment),
        (auth.datarequest_comment_show,   context, request_data_comment),
        (auth.datarequest_comment_list,   None,    request_data_comment),
        (auth.datarequest_comment_list,   context, request_data_comment)
    ])
    def test_everyone_can_create_show_and_index(self, function, context, request_data):
        self.assertTrue(function(context, request_data).get('success', False))

    @parameterized.expand([
        # Data Requests
        (auth.datarequest_update, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, True, True),
        (auth.datarequest_update, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, False, True),
        (auth.datarequest_update, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, True, False),
        (auth.datarequest_update, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, False, False),
        (auth.datarequest_delete, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, True, True),
        (auth.datarequest_delete, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, False, True),
        (auth.datarequest_delete, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, True, False),
        (auth.datarequest_delete, constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, False, False),
        (auth.datarequest_close,  constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, True, True),
        (auth.datarequest_close,  constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'user_id'}, False, True),
        (auth.datarequest_close,  constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, True, False),
        (auth.datarequest_close,  constants.DATAREQUEST_SHOW,                 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, False, False),
        # Comments
        (auth.datarequest_comment_update, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'user_id'}, True, True),
        (auth.datarequest_comment_update, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'user_id'}, False, True),
        (auth.datarequest_comment_update, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, True, False),
        (auth.datarequest_comment_update, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, False, False),
        (auth.datarequest_comment_delete, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'user_id'}, True, True),
        (auth.datarequest_comment_delete, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'user_id'}, False, True),
        (auth.datarequest_comment_delete, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, True, False),
        (auth.datarequest_comment_delete, constants.DATAREQUEST_COMMENT_SHOW, 'user_id', {'id': 'id', 'user_id': 'other_user_id'}, False, False),

    ])
    def test_datarequest_update_delete(self, function, show_function, user_id, request_data, action_called, expected_result):

        user_obj = MagicMock()
        user_obj.id = user_id

        context = {'auth_user_obj': user_obj}

        if action_called:
            initial_request_data = {'id': request_data['id']}
            xyz_show = auth.tk.get_action.return_value
            xyz_show.return_value = request_data
        else:
            initial_request_data = request_data

        result = function(context, initial_request_data).get('success')
        self.assertEquals(expected_result, result)

        if action_called:
            auth.tk.get_action.assert_called_once_with(show_function)
            xyz_show = auth.tk.get_action.return_value
            xyz_show.assert_called_once_with({'ignore_auth': True}, {'id': request_data['id']})
        else:
            self.assertEquals(0, auth.tk.get_action.call_count)
