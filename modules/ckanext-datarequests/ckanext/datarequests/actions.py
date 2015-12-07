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


import ckan.plugins as plugins
import constants
import datetime
import cgi
import db
import logging
import validator

from ckan.lib.mailer import mail_recipient, MailerException
from ckan.lib.i18n import set_lang, get_lang
from ckan.common import g
from pylons import config
from ckan import model

c = plugins.toolkit.c
log = logging.getLogger(__name__)
tk = plugins.toolkit

# Avoid user_show lag
USERS_CACHE = {}


def _get_user(user_id):
    try:
        if user_id in USERS_CACHE:
            return USERS_CACHE[user_id]
        else:
            user = tk.get_action('user_show')({'ignore_auth': True}, {'id': user_id})
            USERS_CACHE[user_id] = user
            return user
    except Exception as e:
        log.warn(e)


def _get_organization(organization_id):
    try:
        organization_show = tk.get_action('organization_show')
        return organization_show({'ignore_auth': True}, {'id': organization_id})
    except Exception as e:
        log.warn(e)


def _get_package(package_id):
    try:
        package_show = tk.get_action('package_show')
        return package_show({'ignore_auth': True}, {'id': package_id})
    except Exception as e:
        log.warn(e)


def _dictize_datarequest(datarequest):
    # Transform time
    open_time = str(datarequest.open_time)
    # Close time can be None and the transformation is only needed when the
    # fields contains a valid date
    close_time = datarequest.close_time
    close_time = str(close_time) if close_time else close_time

    # Convert the data request into a dict
    data_dict = {
        'id': datarequest.id,
        'user_id': datarequest.user_id,
        'title': datarequest.title,
        'description': datarequest.description,
        'organization_id': datarequest.organization_id,
        'open_time': open_time,
        'accepted_dataset_id': datarequest.accepted_dataset_id,
        'close_time': close_time,
        'closed': datarequest.closed,
        'user': _get_user(datarequest.user_id),
        'organization': None,
        'accepted_dataset': None
    }

    if datarequest.organization_id:
        data_dict['organization'] = _get_organization(datarequest.organization_id)

    if datarequest.accepted_dataset_id:
        data_dict['accepted_dataset'] = _get_package(datarequest.accepted_dataset_id)

    return data_dict


def _undictize_datarequest_basic(data_request, data_dict):
    data_request.title = data_dict['title']
    data_request.description = data_dict['description']
    organization = data_dict['organization_id']
    data_request.organization_id = organization if organization else None


def _dictize_comment(comment):

    return {
        'id': comment.id,
        'datarequest_id': comment.datarequest_id,
        'user_id': comment.user_id,
        'comment': comment.comment,
        'time': str(comment.time),
        'user': _get_user(comment.user_id)
    }


def _undictize_comment_basic(comment, data_dict):
    comment.comment = cgi.escape(data_dict.get('comment', ''))
    comment.datarequest_id = data_dict.get('datarequest_id', '')


def _send_comment_notification_mail(recipient_name, recipient_email, data, lang="en"):
    '''
        A helper function to send notification emails to given recipients
    '''

    current_locale = get_lang()
    if lang:
        set_lang(lang)

    from ckanext.datarequests import email_template

    # recreate the request url
    url = str(g.site_url) + tk.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI', action='show', id=data.get("request_id"))
    data["link"] = url

    # fill out the email template
    subject = email_template.subject.format(**data)
    message = email_template.message.format(**data)

    # Finally mail the user and reset locale
    try:
        mail_recipient(recipient_name, recipient_email, subject, message)
    except MailerException, e:
        log.error(e)
    finally:
        set_lang(current_locale)


def _get_organization_admins(group_id, sysadmin=False):
    '''
        A helper function to fetch all the organization's admins.
    '''
    admins = set(model.Session.query(model.User).join(model.Member, model.User.id == model.Member.table_id).
                 filter(model.Member.table_name == "user").filter(model.Member.group_id == group_id).
                 filter(model.Member.state == 'active').filter(model.Member.capacity == 'admin'))

    if sysadmin:
        admins.update(set(model.Session.query(model.User).filter(model.User.sysadmin == True)))  # noqa

    return admins


def datarequest_create(context, data_dict):
    '''
    Action to create a new data request. The function checks the access rights
    of the user before creating the data request. If the user is not allowed
    a NotAuthorized exception will be risen.

    In addition, you should note that the parameters will be checked and an
    exception (ValidationError) will be risen if some of these parameters are
    not valid.

    :param title: The title of the data request
    :type title: string

    :param description: A brief description for your data request
    :type description: string

    :param organization_id: If you want to create the data request in a specific
        organization.
    :type organization_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed)
    :rtype: dict
    '''

    model = context['model']
    session = context['session']

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_CREATE, context, data_dict)

    # Validate data
    validator.validate_datarequest(context, data_dict)

    # Store the data
    data_req = db.DataRequest()
    _undictize_datarequest_basic(data_req, data_dict)
    data_req.user_id = context['auth_user_obj'].id
    data_req.open_time = datetime.datetime.now()

    session.add(data_req)
    session.commit()

    # SEND NOTIFICATION EMAIL
    group_dict = tk.get_action('organization_show')({}, {'id': data_dict['organization_id']})

    # set up a data dict for filling out the email template
    data = {
        "email": context['auth_user_obj'].email,
        "user": context['auth_user_obj'].name,
        "request_title": data_dict.get("title"),
        "request_description": data_dict.get("description"),
        "request_id": data_req.id,
        "organization": group_dict.get("display_name"),
        "organization_lang": group_dict.get("original_language")
    }

    admins = _get_organization_admins(data_dict.get('organization_id', ''))
    for admin in admins:
        if admin:
            lang = data.get("organization_lang", "en")  # send the mail in organization's default lang
            _send_comment_notification_mail(admin.display_name, admin.email, data, lang)

    # Always send a notification mail to website admin
    admin_email = config.get("ckanext-datarequests.datarequest_notifications_admin_email", None)
    if admin_email:
        # Add 4th parameter lang (fi/sv/en) for internationalizerd email templates
        log.debug("Sending datarequest notification email to avoindata-admin")
        _send_comment_notification_mail("Avoindata-admin", admin_email, data)

    return _dictize_datarequest(data_req)


def datarequest_show(context, data_dict):
    '''
    Action to retrieve the information of a data request. The only required
    parameter is the id of the data request. A NotFound exception will be
    risen if the id is not found.

    Access rights will be checked before returning the information and an
    exception will be risen (NotAuthorized) if the user is not authorized.

    :param id: The id of the data request to be shown
    :type id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed)
    :rtype: dict
    '''

    model = context['model']
    datarequest_id = data_dict.get('id', '')

    if not datarequest_id:
        raise tk.ValidationError('Data Request ID has not been included')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_SHOW, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound('Data Request %s not found in the data base' % datarequest_id)

    data_req = result[0]
    data_dict = _dictize_datarequest(data_req)

    return data_dict


def datarequest_update(context, data_dict):
    '''
    Action to update a dara request. The function checks the access rights of
    the user before updating the data request. If the user is not allowed
    a NotAuthorized exception will be risen.

    In addition, you should note that the parameters will be checked and an
    exception (ValidationError) will be risen if some of these parameters are
    not valid.

    :param id: The id of the data request to be updated
    :type id: string

    :param title: The title of the data request
    :type title: string

    :param description: A brief description for your data request
    :type description: string

    :param organiztion_id: If you want to create the data request in a specific
        organization.
    :type organization_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed)
    :rtype: dict
    '''

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    if not datarequest_id:
        raise tk.ValidationError('Data Request ID has not been included')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_UPDATE, context, data_dict)

    # Get the initial data
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound('Data Request %s not found in the data base' % datarequest_id)

    data_req = result[0]

    # Avoid the validator to return an error when the user does not change the title
    context['avoid_existing_title_check'] = data_req.title == data_dict['title']

    # Validate data
    validator.validate_datarequest(context, data_dict)

    # Set the data provided by the user in the data_red
    _undictize_datarequest_basic(data_req, data_dict)

    session.add(data_req)
    session.commit()

    return _dictize_datarequest(data_req)


def datarequest_index(context, data_dict):
    '''
    Returns a list with the existing data requests. Rights access will be checked
    before returning the results. If the user is not allowed, a NotAuthorized
    exception will be risen.

    :param organization_id: This parameter is optional and allows users
        to filter the results by organization
    :type organization_id: string

    :param user_id: This parameter is optional and allows users
        to filter the results by user
    :type organization_id: string

    :param closed: This parameter is optional and allos users to filter
        the result by the data request status (open or closed)
    :type closed: bool

    :param offset: The first element to be returned (0 by default)
    :type offset: int

    :param limit: The max number of data requests to be returned (10 by default)
    :type limit: init

    :returns: A dict with three fields: result (a list of data requests),
        facets (a list of the facets that can be used) and count (the total
        number of existing data requests)
    :rtype: dict
    '''

    model = context['model']
    organization_show = tk.get_action('organization_show')
    user_show = tk.get_action('user_show')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_INDEX, context, data_dict)

    # Get the organization
    organization_id = data_dict.get('organization_id', None)
    params = {}
    if organization_id:
        # Get organization ID (in some cases the organization name is received)
        organization_id = organization_show({'ignore_auth': True}, {'id': organization_id}).get('id')

        # Include organization ID into the parameters to filter the database query
        params['organization_id'] = organization_id

    user_id = data_dict.get('user_id', None)
    if user_id:
        # Get user ID (the user name is received)
        user_id = user_show({'ignore_auth': True}, {'id': user_id}).get('id')

        # Include user ID into the parameters to filter the database query
        params['user_id'] = user_id

    # Filter by state
    closed = data_dict.get('closed', None)
    if closed is not None:
        params['closed'] = closed

    # Call the function
    db_datarequests = db.DataRequest.get_ordered_by_date(**params)

    # Dictize the results
    offset = data_dict.get('offset', 0)
    limit = data_dict.get('limit', constants.DATAREQUESTS_PER_PAGE)
    datarequests = []
    for data_req in db_datarequests[offset:offset + limit]:
        datarequests.append(_dictize_datarequest(data_req))

    # Facets
    no_processed_organization_facet = {}
    CLOSED = 'Closed'   # noqa
    OPEN = 'Open'       # noqa
    no_processed_state_facet = {CLOSED: 0, OPEN: 0}
    for data_req in db_datarequests:
        if data_req.organization_id:
            # Facets
            if data_req.organization_id in no_processed_organization_facet:
                no_processed_organization_facet[data_req.organization_id] += 1
            else:
                no_processed_organization_facet[data_req.organization_id] = 1

        no_processed_state_facet[CLOSED if data_req.closed else OPEN] += 1

    # Format facets
    organization_facet = []
    for organization_id in no_processed_organization_facet:
        try:
            organization = organization_show({'ignore_auth': True}, {'id': organization_id})
            organization_facet.append({
                'name': organization.get('name'),
                'display_name': organization.get('display_name'),
                'count': no_processed_organization_facet[organization_id]
            })
        except:
            pass

    state_facet = []
    for state in no_processed_state_facet:
        if no_processed_state_facet[state]:
            state_facet.append({
                'name': state.lower(),
                'display_name': state,
                'count': no_processed_state_facet[state]
            })

    result = {
        'count': len(db_datarequests),
        'facets': {},
        'result': datarequests
    }

    # Facets can only be included if they contain something
    if organization_facet:
        result['facets']['organization'] = {'items': organization_facet}

    if state_facet:
        result['facets']['state'] = {'items': state_facet}

    return result


def datarequest_delete(context, data_dict):
    '''
    Action to delete a new dara request. The function checks the access rights
    of the user before deleting the data request. If the user is not allowed
    a NotAuthorized exception will be risen.

    :param id: The id of the data request to be updated
    :type id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed)
    :rtype: dict
    '''

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError('Data Request ID has not been included')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_DELETE, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound('Data Request %s not found in the data base' % datarequest_id)

    data_req = result[0]
    session.delete(data_req)
    session.commit()

    return _dictize_datarequest(data_req)


def datarequest_close(context, data_dict):
    '''
    Action to close a data request. Access rights will be checked before closing the
    data request. If the user is not allowed, a NotAuthorized exception will be risen.

    :param id: The id of the data request to be closed
    :type id: string

    :param accepted_dataset_id: The ID of the dataset accepted as solution for this
        data request
    :type accepted_dataset_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed)
    :rtype: dict

    '''

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError('Data Request ID has not been included')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_CLOSE, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound('Data Request %s not found in the data base' % datarequest_id)

    # Validate data
    validator.validate_datarequest_closing(context, data_dict)

    data_req = result[0]

    # Was the data request previously closed?
    if data_req.closed:
        raise tk.ValidationError(['This Data Request is already closed'])

    data_req.closed = True
    data_req.accepted_dataset_id = data_dict.get('accepted_dataset_id', None)
    data_req.close_time = datetime.datetime.now()

    session.add(data_req)
    session.commit()

    return _dictize_datarequest(data_req)


def datarequest_comment(context, data_dict):
    '''
    Action to create a comment in a data request. Access rights will be checked before
    creating the comment and a NotAuthorized exception will be risen if the user is not
    allowed to create the comment

    :param datarequest_id: The ID of the datarequest to be commented
    :type id: string

    :param comment: The comment to be added to the data request
    :type comment: string

    :returns: A dict with the data request comment (id, user_id, datarequest_id, time
        and comment)
    :rtype: dict

    '''

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('datarequest_id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError(['Data Request ID has not been included'])

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_COMMENT, context, data_dict)

    # Validate comment
    validator.validate_comment(context, data_dict)

    # Store the data
    comment = db.Comment()
    _undictize_comment_basic(comment, data_dict)
    comment.user_id = context['auth_user_obj'].id
    comment.time = datetime.datetime.now()

    session.add(comment)
    session.commit()

    return _dictize_comment(comment)


def datarequest_comment_show(context, data_dict):
    '''
    Action to retrieve a comment. Access rights will be checked before getting the
    comment and a NotAuthorized exception will be risen if the user is not allowed
    to get the comment

    :param id: The ID of the comment to be retrieved
    :type id: string

    :returns: A dict with the following fields: id, user_id, datarequest_id, time
        and comment
    :rtype: dict
    '''

    model = context['model']
    comment_id = data_dict.get('id', '')

    # Check id
    if not comment_id:
        raise tk.ValidationError(['Comment ID has not been included'])

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_COMMENT_SHOW, context, data_dict)

    # Get comments
    result = db.Comment.get(id=comment_id)
    if not result:
        raise tk.ObjectNotFound('Comment %s not found in the data base' % comment_id)

    return _dictize_comment(result[0])


def datarequest_comment_list(context, data_dict):
    '''
    Action to retrieve all the comments of a data request. Access rights will be checked before
    getting the comments and a NotAuthorized exception will be risen if the user is not
    allowed to read the comments

    :param datarequest_id: The ID of the datarequest whose comments want to be retrieved
    :type id: string

    :returns: A list with all the comments of a data request. Every comment is a dict with the
    following fields: id, user_id, datarequest_id, time and comment
    :rtype: list
    '''

    model = context['model']
    datarequest_id = data_dict.get('datarequest_id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError('Data Request ID has not been included')

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_COMMENT_LIST, context, data_dict)

    # Get comments
    comments_db = db.Comment.get_ordered_by_date(datarequest_id=datarequest_id)

    comments_list = []
    for comment in comments_db:
        comments_list.append(_dictize_comment(comment))

    return comments_list


def datarequest_comment_update(context, data_dict):
    '''
    Action to update a comment of a data request. Access rights will be checked before
    updating the comment and a NotAuthorized exception will be risen if the user is not
    allowed to update the comment

    :param id: The ID of the comment to be updated
    :type id: string

    :param comment: The comment to be added to the data request
    :type comment: string

    :returns: A dict with the data request comment (id, user_id, datarequest_id, time
        and comment)
    :rtype: dict
    '''

    model = context['model']
    session = context['session']
    comment_id = data_dict.get('id', '')

    if not comment_id:
        raise tk.ValidationError(['Comment ID has not been included'])

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_COMMENT_UPDATE, context, data_dict)

    # Get the data request
    result = db.Comment.get(id=comment_id)
    if not result:
        raise tk.ObjectNotFound('Comment %s not found in the data base' % comment_id)

    comment = result[0]

    # Validate data
    validator.validate_comment(context, data_dict)

    # Set the data provided by the user in the data_red
    _undictize_comment_basic(comment, data_dict)

    session.add(comment)
    session.commit()

    return _dictize_comment(comment)


def datarequest_comment_delete(context, data_dict):
    '''
    Action to delete a comment of a data request. Access rights will be checked before
    deleting the comment and a NotAuthorized exception will be risen if the user is not
    allowed to delete the comment

    :param id: The ID of the comment to be deleted
    :type id: string

    :returns: A dict with the data request comment (id, user_id, datarequest_id, time
        and comment)
    :rtype: dict
    '''

    model = context['model']
    session = context['session']
    comment_id = data_dict.get('id', '')

    if not comment_id:
        raise tk.ValidationError(['Comment ID has not been included'])

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.DATAREQUEST_COMMENT_DELETE, context, data_dict)

    # Get the data request
    result = db.Comment.get(id=comment_id)
    if not result:
        raise tk.ObjectNotFound('Comment %s not found in the data base' % comment_id)

    comment = result[0]

    session.delete(comment)
    session.commit()

    return _dictize_comment(comment)
