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

import logging

import ckan.lib.base as base
import ckan.model as model
import ckan.plugins as plugins
import ckan.lib.helpers as helpers
import ckanext.datarequests.constants as constants
import functools
import re

from ckan.common import request
from urllib import urlencode


_link = re.compile(r'(?:(https?://)|(www\.))(\S+\b/?)([!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]*)(\s|$)', re.I)

log = logging.getLogger(__name__)
tk = plugins.toolkit
c = tk.c


def convert_links(text):
    def replace(match):
        groups = match.groups()
        protocol = groups[0] or ''  # may be None
        www_lead = groups[1] or ''  # may be None
        return '<a href="{0}{1}{2}" target="_blank">{0}{1}{2}</a>{3}{4}'.format(
            protocol, www_lead, *groups[2:])
    return _link.sub(replace, text)


def _get_errors_summary(errors):
    errors_summary = {}

    for key, error in errors.items():
        errors_summary[key] = ', '.join(error)

    return errors_summary


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_url(params):
    url = helpers.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                          action='index')
    return url_with_params(url, params)


def org_datarequest_url(params, id):
    url = helpers.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                          action='organization_datarequests', id=id)
    return url_with_params(url, params)


def user_datarequest_url(params, id):
    url = helpers.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                          action='user_datarequests', id=id)
    return url_with_params(url, params)


class DataRequestsUI(base.BaseController):

    def _get_context(self):
        return {'model': model, 'session': model.Session,
                'user': c.user, 'auth_user_obj': c.userobj}

    def _show_index(self, user_id, organization_id, include_organization_facet, url_func, file_to_render):

        def pager_url(q=None, page=None):
            params = list()
            params.append(('page', page))
            return url_func(params)

        try:
            context = self._get_context()
            page = int(request.GET.get('page', 1))
            limit = constants.DATAREQUESTS_PER_PAGE
            offset = (page - 1) * constants.DATAREQUESTS_PER_PAGE
            data_dict = {'offset': offset, 'limit': limit}

            state = request.GET.get('state', None)
            if state:
                data_dict['closed'] = True if state == 'closed' else False

            if organization_id:
                data_dict['organization_id'] = organization_id

            if user_id:
                data_dict['user_id'] = user_id

            tk.check_access(constants.DATAREQUEST_INDEX, context, data_dict)
            datarequests_list = tk.get_action(constants.DATAREQUEST_INDEX)(context, data_dict)
            c.datarequest_count = datarequests_list['count']
            c.datarequests = datarequests_list['result']
            c.search_facets = datarequests_list['facets']
            c.page = helpers.Page(
                collection=datarequests_list['result'],
                page=page,
                url=pager_url,
                item_count=datarequests_list['count'],
                items_per_page=limit
            )
            c.facet_titles = {
                'state': tk._('State'),
            }

            # Organization facet cannot be shown when the user is viewing an org
            if include_organization_facet is True:
                c.facet_titles['organization'] = tk._('Organizations')

            return tk.render(file_to_render)
        except ValueError as e:
            # This exception should only occur if the page value is not valid
            log.warn(e)
            tk.abort(400, tk._('"page" parameter must be an integer'))
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('Unauthorized to list Data Requests'))

    def index(self):
        return self._show_index(None, request.GET.get('organization', ''), True, search_url, 'datarequests/index.html')

    def _process_post(self, action, context):
        # If the user has submitted the form, the data request must be created
        if request.POST:
            data_dict = {}
            data_dict['title'] = request.POST.get('title', '')
            data_dict['description'] = request.POST.get('description', '')
            data_dict['organization_id'] = request.POST.get('organization_id', '')

            if action == constants.DATAREQUEST_UPDATE:
                data_dict['id'] = request.POST.get('id', '')

            try:
                result = tk.get_action(action)(context, data_dict)
                tk.response.status_int = 302
                tk.response.location = '/data/%s/%s' % (constants.DATAREQUESTS_MAIN_PATH,
                                                   result['id'])

            except tk.ValidationError as e:
                log.warn(e)
                # Fill the fields that will display some information in the page
                c.datarequest = {
                    'id': data_dict.get('id', ''),
                    'title': data_dict.get('title', ''),
                    'description': data_dict.get('description', ''),
                    'organization_id': data_dict.get('organization_id', '')
                }
                c.errors = e.error_dict
                c.errors_summary = _get_errors_summary(c.errors)

    def new(self):
        context = self._get_context()

        # Basic intialization
        c.datarequest = {}
        c.errors = {}
        c.errors_summary = {}

        # Check access
        try:
            tk.check_access(constants.DATAREQUEST_CREATE, context, None)
            self._process_post(constants.DATAREQUEST_CREATE, context)

            # The form is always rendered
            return tk.render('datarequests/new.html')

        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('Unauthorized to create a Data Request'))

    def show(self, id):
        data_dict = {'id': id}
        context = self._get_context()

        try:
            tk.check_access(constants.DATAREQUEST_SHOW, context, data_dict)
            c.datarequest = tk.get_action(constants.DATAREQUEST_SHOW)(context, data_dict)

            context_ignore_auth = context.copy()
            context_ignore_auth['ignore_auth'] = True

            return tk.render('datarequests/show.html')
        except tk.ObjectNotFound as e:
            tk.abort(404, tk._('Data Request %s not found') % id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to view the Data Request %s'
                               % id))

    def update(self, id):
        data_dict = {'id': id}
        context = self._get_context()

        # Basic intialization
        c.datarequest = {}
        c.errors = {}
        c.errors_summary = {}

        try:
            tk.check_access(constants.DATAREQUEST_UPDATE, context, data_dict)
            c.datarequest = tk.get_action(constants.DATAREQUEST_SHOW)(context, data_dict)
            c.original_title = c.datarequest.get('title')
            self._process_post(constants.DATAREQUEST_UPDATE, context)
            return tk.render('datarequests/edit.html')
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Data Request %s not found') % id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to update the Data Request %s'
                               % id))

    def delete(self, id):
        data_dict = {'id': id}
        context = self._get_context()

        try:
            tk.check_access(constants.DATAREQUEST_DELETE, context, data_dict)
            datarequest = tk.get_action(constants.DATAREQUEST_DELETE)(context, data_dict)
            tk.response.status_int = 302
            tk.response.location = '/data/%s' % constants.DATAREQUESTS_MAIN_PATH
            helpers.flash_notice(tk._('Data Request %s deleted correctly') % datarequest.get('title', ''))
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Data Request %s not found') % id)
        except tk.NotAuthorized as e:
            log.warn(e) 
            tk.abort(403, tk._('You are not authorized to delete the Data Request %s'
                               % id))

    def organization_datarequests(self, id):
        context = self._get_context()

        try:
          c.group_dict = tk.get_action('organization_show')(context, {'id': id})
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Organization was not found'))

        url_func = functools.partial(org_datarequest_url, id=id)
        return self._show_index(None, id, False, url_func, 'organization/datarequests.html')

    def user_datarequests(self, id):
        context = self._get_context()
        c.user_dict = tk.get_action('user_show')(context, {'id': id, 'include_num_followers': True})
        url_func = functools.partial(user_datarequest_url, id=id)
        return self._show_index(id, request.GET.get('organization', ''), True, url_func, 'user/datarequests.html')

    def close(self, id):
        data_dict = {'id': id}
        context = self._get_context()

        # Basic intialization
        c.datarequest = {}

        def _return_page(errors={}, errors_summary={}):
            # Get datasets (if the data req belongs to an organization, only the one that
            # belongs to the organization are shown)
            organization_id = c.datarequest.get('organization_id', '')
            if organization_id:
                base_datasets = tk.get_action('organization_show')({'ignore_auth': True}, {'id': organization_id})['packages']
            else:
                # FIXME: At this time, only the 500 last modified/created datasets are retrieved.
                # We assume that a user will close their data request with a recently added or modified dataset
                # In the future, we should fix this with an autocomplete form...
                # Expected for CKAN 2.3
                base_datasets = tk.get_action('package_search')({'ignore_auth': True}, {'rows': 500})['results']

            c.datasets = []
            c.errors = errors
            c.errors_summary = errors_summary
            for dataset in base_datasets:
                c.datasets.append({'name': dataset.get('name'), 'title': dataset.get('title')})

            return tk.render('datarequests/close.html')

        try:
            tk.check_access(constants.DATAREQUEST_CLOSE, context, data_dict)
            c.datarequest = tk.get_action(constants.DATAREQUEST_SHOW)(context, data_dict)

            if c.datarequest.get('closed', False):
                tk.abort(403, tk._('This data request is already closed'))
            elif request.POST:
                data_dict = {}
                data_dict['accepted_dataset_id'] = request.POST.get('accepted_dataset_id', None)
                data_dict['id'] = id

                tk.get_action(constants.DATAREQUEST_CLOSE)(context, data_dict)
                tk.response.status_int = 302
                tk.response.location = '/data/%s/%s' % (constants.DATAREQUESTS_MAIN_PATH, data_dict['id'])
            else:   # GET
                return _return_page()

        except tk.ValidationError as e:     # Accepted Dataset is not valid
            log.warn(e)
            errors_summary = _get_errors_summary(e.error_dict)
            return _return_page(e.error_dict, errors_summary)
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Data Request %s not found') % id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to close the Data Request %s'
                               % id))

    def comment(self, id):
        try:
            context = self._get_context()
            data_dict_comment_list = {'datarequest_id': id}
            data_dict_dr_show = {'id': id}
            tk.check_access(constants.DATAREQUEST_COMMENT_LIST, context, data_dict_comment_list)

            # Raises 404 Not Found if the data request does not exist
            c.datarequest = tk.get_action(constants.DATAREQUEST_SHOW)(context, data_dict_dr_show)

            comment = request.POST.get('comment', '')
            comment_id = request.POST.get('comment-id', '')

            if request.POST:
                action = constants.DATAREQUEST_COMMENT
                action_text = 'comment'

                if comment_id:
                    action = constants.DATAREQUEST_COMMENT_UPDATE
                    action_text = 'update comment'

                try:
                    comment_data_dict = {'datarequest_id': id, 'comment': comment, 'id': comment_id}
                    comment = tk.get_action(action)(context, comment_data_dict)
                except tk.NotAuthorized as e:
                    log.warn(e)
                    tk.abort(403, tk._('You are not authorized to %s' % action_text))
                except tk.ValidationError as e:
                    log.warn(e)
                    c.errors = e.error_dict
                    c.errors_summary = _get_errors_summary(c.errors)
                    c.comment = comment
                except tk.ObjectNotFound as e:
                    log.warn(e)
                    tk.abort(404, tk._(str(e)))
                # Other exceptions are not expected. Otherwise, the request will fail.

            # Comments should be retrieved once that the comment has been created
            get_comments_data_dict = {'datarequest_id': id}
            c.comments = tk.get_action(constants.DATAREQUEST_COMMENT_LIST)(context, get_comments_data_dict)

            # Replace URLs by links
            # Replace new lines by HTML line break
            for comment in c.comments:
                comment['comment'] = convert_links(comment['comment'])
                comment['comment'] = comment['comment'].replace('\n', '<br/>')

            return tk.render('datarequests/comment.html')

        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Data Request %s not found' % id))

        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to list the comments of the Data Request %s'
                               % id))

    def delete_comment(self, datarequest_id, comment_id):
        try:
            context = self._get_context()
            data_dict = {'id': comment_id}
            tk.check_access(constants.DATAREQUEST_COMMENT_DELETE, context, data_dict)
            tk.get_action(constants.DATAREQUEST_COMMENT_DELETE)(context, data_dict)
            tk.response.status_int = 302
            tk.response.location = '/data/%s/comment/%s' % (constants.DATAREQUESTS_MAIN_PATH, datarequest_id)
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Comment %s not found') % comment_id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to delete this comment'))
