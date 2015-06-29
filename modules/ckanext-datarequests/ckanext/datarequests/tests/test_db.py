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

import unittest
import ckanext.datarequests.db as db

from mock import MagicMock
from nose_parameterized import parameterized


class DBTest(unittest.TestCase):

    def setUp(self):
        # Restart databse initial status
        db.DataRequest = None
        db.Comment = None

        # Create mocks
        self._sa = db.sa
        db.sa = MagicMock()

        self._func = db.func
        db.func = MagicMock()

    def tearDown(self):
        db.Comment = None
        db.DataRequest = None
        db.sa = self._sa
        db.func = self._func

    def _test_get(self, table):
        '''
        Aux method for Comment and Data Requests
        '''
        db_response = [MagicMock(), MagicMock(), MagicMock()]

        query_result = MagicMock()
        query_result.all.return_value = db_response

        final_query = MagicMock()
        final_query.filter_by.return_value = query_result

        query = MagicMock()
        query.autoflush = MagicMock(return_value=final_query)

        model = MagicMock()
        model.DomainObject = object
        model.Session.query = MagicMock(return_value=query)

        # Init the database
        db.init_db(model)

        # Call the method
        params = {
            'title': 'Default Title',
            'organization_id': 'example_uuid_v4'
        }
        result = getattr(db, table).get(**params)

        # Assertions
        self.assertEquals(db_response, result)
        final_query.filter_by.assert_called_once_with(**params)

    def _test_get_ordered_by_date(self, table, time_column):
        db_response = [MagicMock(), MagicMock(), MagicMock()]

        query_result = MagicMock()
        query_result.all.return_value = db_response

        no_ordered = MagicMock()
        no_ordered.order_by.return_value = query_result

        final_query = MagicMock()
        final_query.filter_by.return_value = no_ordered

        query = MagicMock()
        query.autoflush = MagicMock(return_value=final_query)

        model = MagicMock()
        model.DomainObject = object
        model.Session.query = MagicMock(return_value=query)

        # Init the database
        db.init_db(model)
        # Mapping
        table = getattr(db, table)
        time_column_value = MagicMock()
        setattr(table, time_column, time_column_value)

        # Call the method
        params = {
            'title': 'Default Title',
            'organization_id': 'example_uuid_v4'
        }
        result = table.get_ordered_by_date(**params)

        # Assertions
        self.assertEquals(db_response, result)
        no_ordered.order_by.assert_called_once_with(time_column_value.desc())
        final_query.filter_by.assert_called_once_with(**params)

    def test_initdb_not_initialized(self):

        table_data_request = MagicMock()
        table_comment = MagicMock()

        db.sa.Table = MagicMock(side_effect=[table_data_request, table_comment])

        # Call the function
        model = MagicMock()
        db.init_db(model)

        # Assert that table method has been called
        self.assertEquals(2, db.sa.Table.call_count)
        model.meta.mapper.assert_any_call(db.DataRequest, table_data_request)
        model.meta.mapper.assert_any_call(db.Comment, table_comment)

    def test_initdb_initialized(self):
        db.DataRequest = MagicMock()
        db.Comment = MagicMock()

        # Call the function
        model = MagicMock()
        db.init_db(model)

        # Assert that table method has been called
        self.assertEquals(0, db.sa.Table.call_count)
        self.assertEquals(0, model.meta.mapper.call_count)

    def test_datarequest_get(self):
        self._test_get('DataRequest')

    @parameterized.expand([
        (None, False),
        (1,    True)
    ])
    def test_datarequest_exist(self, first_result, expected_result):

        title = 'DataRequest Title'

        # Prepare the mocks
        def _lower(text):
            # If expected_result == true it's because lower is supossed
            # to return the same result in the two calls
            if expected_result:
                return title.lower()
            else:
                return text

        db.func.lower.side_effect = _lower

        # Query
        query_result = MagicMock()
        query_result.first.return_value = first_result

        final_query = MagicMock()
        final_query.filter.return_value = query_result

        query = MagicMock()
        query.autoflush = MagicMock(return_value=final_query)

        model = MagicMock()
        model.DomainObject = object
        model.Session.query = MagicMock(return_value=query)

        # Init the database
        db.init_db(model)

        # Call the method
        db.DataRequest.title = 'TITLE'
        result = db.DataRequest.datarequest_exists(title)

        # Assertion
        self.assertEquals(expected_result, result)
        db.func.lower.assert_any_call(db.DataRequest.title)
        db.func.lower.assert_any_call(title)
        # If expected_result == true is because lower is supossed
        # to return the same result in the two calls and the
        # equalization of these results must be True
        final_query.filter.assert_called_once_with(expected_result)

    def test_datarequest_get_ordered_by_date(self):
        self._test_get_ordered_by_date('DataRequest', 'open_time')

    def test_comment_get(self):
        self._test_get('Comment')

    def test_comment_get_ordered_by_date(self):
        self._test_get_ordered_by_date('Comment', 'time')
