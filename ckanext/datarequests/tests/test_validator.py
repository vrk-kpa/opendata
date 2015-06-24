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

import ckanext.datarequests.validator as validator
import unittest
import random

from mock import MagicMock
from nose_parameterized import parameterized


def generate_string(length):
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                   for i in range(length))


class ValidatorTest(unittest.TestCase):

    def setUp(self):
        self.context = MagicMock()
        self.request_data = {
            'title': 'Example Title',
            'description': 'Example description',
            'organization_id': 'uuid-example'
        }

        # Mocks
        self._tk = validator.tk
        validator.tk = MagicMock()
        validator.tk.ValidationError = self._tk.ValidationError
        validator.tk._ = self._tk._

        self._db = validator.db
        validator.db = MagicMock()
        validator.db.DataRequest.datarequest_exists.return_value = False

    def tearDown(self):
        validator.tk = self._tk

    @parameterized.expand([
        (True,),
        (False,)
    ])
    def test_validate_valid_data_request(self, avoid_existing_title_check):
        context = {'avoid_existing_title_check': avoid_existing_title_check}
        self.assertIsNone(validator.validate_datarequest(context, self.request_data))
        validator.tk.get_validator.assert_called_once_with('group_id_exists')
        group_validator = validator.tk.get_validator.return_value
        group_validator.assert_called_once_with(self.request_data['organization_id'], context)

        if avoid_existing_title_check:
            self.assertEquals(0, validator.db.DataRequest.datarequest_exists.call_count)
        else:
            validator.db.DataRequest.datarequest_exists.assert_called_once_with(self.request_data['title'])

    @parameterized.expand([
        ('Title', generate_string(validator.constants.NAME_MAX_LENGTH + 1), False,
            'Title must be a maximum of %d characters long' % validator.constants.NAME_MAX_LENGTH),
        ('Title', '', False, 'Title cannot be empty'),
        ('Title', 'DR Example Tile', True, 'That title is already in use'),
        ('Description', generate_string(validator.constants.DESCRIPTION_MAX_LENGTH + 1), False,
            'Description must be a maximum of %d characters long' % validator.constants.DESCRIPTION_MAX_LENGTH),

    ])
    def test_validate_name_description(self, field, value, title_exists, excepction_msg):
        context = {}
        # request_data fields are always in lowercase
        self.request_data[field.lower()] = value
        validator.db.DataRequest.datarequest_exists.return_value = title_exists

        with self.assertRaises(self._tk.ValidationError) as c:
            validator.validate_datarequest(context, self.request_data)

        self.assertEquals({field: [excepction_msg]},
                          c.exception.error_dict)

    def test_invalid_org(self):
        context = {}
        org_validator = validator.tk.get_validator.return_value
        org_validator.side_effect = self._tk.ValidationError({'Organization': 'Invalid ORG'})

        with self.assertRaises(self._tk.ValidationError) as c:
            validator.validate_datarequest(context, self.request_data)

        self.assertEquals({'Organization': ['Organization is not valid']},
                          c.exception.error_dict)

    def test_missing_org(self):
        self.request_data['organization_id'] = ''
        context = MagicMock()
        self.assertIsNone(validator.validate_datarequest(context, self.request_data))
        self.assertEquals(0, validator.tk.get_validator.call_count)

    def test_close_invalid_accepted_dataset(self):
        context = {}
        accepted_ds_id = 'accepted_ds_uuidv4'
        package_validator = validator.tk.get_validator.return_value
        package_validator.side_effect = self._tk.ValidationError({'Dataset': 'Invalid Dataset'})

        # Call the function (exception expected)
        with self.assertRaises(self._tk.ValidationError) as c:
            validator.validate_datarequest_closing(context, {'id': 'dr_id', 'accepted_dataset_id': accepted_ds_id})

        # Check that the correct validator is called
        validator.tk.get_validator.assert_called_once_with('package_name_exists')

        # Check that the validator has been properly called
        package_validator.assert_called_once_with(accepted_ds_id, context)
        self.assertEquals({'Accepted Dataset': ['Dataset not found']},
                          c.exception.error_dict)

    def test_close_valid(self):
        context = {}
        accepted_ds_id = 'accepted_ds_uuidv4'
        package_validator = validator.tk.get_validator.return_value

        # Call the function
        validator.validate_datarequest_closing(context, {'id': 'dr_id', 'accepted_dataset_id': accepted_ds_id})

        # Check that the correct validator is called
        validator.tk.get_validator.assert_called_once_with('package_name_exists')

        # Check that the package existence has been checked
        package_validator.assert_called_once_with(accepted_ds_id, context)

    @parameterized.expand([
        ({},              'Comment', 'Comments must be a minimum of 1 character long'),
        ({'comment': ''}, 'Comment', 'Comments must be a minimum of 1 character long'),
        ({'comment': generate_string(validator.constants.COMMENT_MAX_LENGTH + 1)}, 'Comment',
            'Comments must be a maximum of %d characters long' % validator.constants.COMMENT_MAX_LENGTH)
    ])
    def test_comment_invalid(self, request_data, field, message):
        context = {}
        request_data['datarequest_id'] = 'exmaple'

        # Call the function
        with self.assertRaises(self._tk.ValidationError) as c:
            validator.validate_comment(context, request_data)

        self.assertEquals({field: [message]}, c.exception.error_dict)

    def test_comment_invalid_datarequest(self):
        datarequest_show = validator.tk.get_action.return_value
        datarequest_show.side_effect = self._tk.ObjectNotFound('Store Not found')

        self.test_comment_invalid({'datarequest_id': 'non_existing_dr'}, 'Data Request',
                                  'Data Request not found')

    def test_comment_valid(self):
        request_data = {
            'datarequest_id': 'uuid4',
            'comment': 'Example comment'
        }

        validator.validate_comment({}, request_data)
