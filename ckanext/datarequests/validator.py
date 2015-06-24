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

import constants
import ckan.plugins.toolkit as tk
import ckanext.datarequests.db as db


def validate_datarequest(context, request_data):

    errors = {}

    # Check name
    if len(request_data['title']) > constants.NAME_MAX_LENGTH:
        errors['Title'] = [tk._('Title must be a maximum of %d characters long') % constants.NAME_MAX_LENGTH]

    if not request_data['title']:
        errors['Title'] = [tk._('Title cannot be empty')]

    # Title is only checked in the database when it's correct
    avoid_existing_title_check = context['avoid_existing_title_check'] if 'avoid_existing_title_check' in context else False

    if 'Title' not in errors and not avoid_existing_title_check:
        if db.DataRequest.datarequest_exists(request_data['title']):
            errors['Title'] = ['That title is already in use']

    # Check description
    if len(request_data['description']) > constants.DESCRIPTION_MAX_LENGTH:
        errors['Description'] = [tk._('Description must be a maximum of %d characters long') % constants.DESCRIPTION_MAX_LENGTH]

    # Check organization
    if request_data['organization_id']:
        try:
            tk.get_validator('group_id_exists')(request_data['organization_id'], context)
        except Exception:
            errors['Organization'] = ['Organization is not valid']

    if len(errors) > 0:
        raise tk.ValidationError(errors)


def validate_datarequest_closing(context, request_data):

    accepted_dataset_id = request_data.get('accepted_dataset_id', '')
    if accepted_dataset_id:
        try:
            tk.get_validator('package_name_exists')(accepted_dataset_id, context)
        except Exception:
            raise tk.ValidationError({'Accepted Dataset': ['Dataset not found']})


def validate_comment(context, request_data):
    comment = request_data.get('comment', '')

    # Check if the data request exists
    try:
        tk.get_action(constants.DATAREQUEST_SHOW)(context, {'id': request_data['datarequest_id']})
    except Exception:
        raise tk.ValidationError({'Data Request': [tk._('Data Request not found')]})

    if not comment or len(comment) <= 0:
        raise tk.ValidationError({'Comment': [tk._('Comments must be a minimum of 1 character long')]})

    if len(comment) > constants.COMMENT_MAX_LENGTH:
        raise tk.ValidationError({'Comment': [tk._('Comments must be a maximum of %d characters long') % constants.COMMENT_MAX_LENGTH]})
