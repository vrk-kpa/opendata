from ckan import logic
from ckan.plugins import toolkit
from ckan.logic import auth, NotFound, ValidationError, side_effect_free
from ckan.common import _
from ckan.lib.navl.dictization_functions import validate
from ckan.lib.dictization import model_save, model_dictize
from ckan.lib.dictization.model_dictize import user_dictize
from ckan.lib import uploader, munge, helpers
from ckan.common import c
from ckan.plugins.core import get_plugin

import requests
import json
import logging
import sqlalchemy
import sqlalchemy.sql
from ckanext.ytp.converters import to_list_json
from ckanext.ytp.tools import add_languages_modify, add_translation_modify_schema

from paste.deploy.converters import asbool


_select = sqlalchemy.sql.select
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case

log = logging.getLogger(__name__)


# Insert here the fields that are localized
_localized_fields = ['job_title', 'about']


def _add_user_extras(user_obj, user_dict):
    for key, value in user_obj.extras.iteritems():
        if key in user_dict:
            log.warning("Trying to override user data with extra variable '%s'", key)
            continue
        if key in ('blog', 'www_page', 'translations'):
            if value:
                user_dict[key] = json.loads(value)
        else:
            user_dict[key] = value

    image_url = user_dict.get('image_url', None)
    user_dict['image_display_url'] = image_url
    if image_url and not image_url.startswith('http'):
        image_url = munge.munge_filename(image_url)
        user_dict['image_display_url'] = helpers.url_for_static(
            'uploads/user/%s' % user_dict.get('image_url'),
            qualified=True
        )
    return user_dict


def _update_drupal_user(context, data_dict):
    resource = 'user'
    path = 'user_2'
    fullname = data_dict.get('fullname')
    apikey = data_dict.get('_apikey')

    try:
        ytp_drupal = get_plugin('ytp_drupal')
        if not ytp_drupal or not c.user:
            log.error('ytp_drupal not found')
            raise NotFound
        drupal7 = get_plugin('drupal7')
        if not drupal7:
            log.error('drupal7 not found')
            raise NotFound
        host = drupal7.get_domain()
        log.warning('host: ' + host)
        # Get Drupal cookie from cookies
        session_cookie = ytp_drupal.get_drupal_session_cookie()
        cookie_header = session_cookie[0] + "=" + session_cookie[1]
        token = ytp_drupal.get_drupal_session_token(host, path, cookie_header)
        duid = str(ytp_drupal.get_drupal_user_id(c.user))
        update_url = 'https://' + host + '/' + path + '/' + resource + '/' + duid + '.json'
        payload = {"field_fullname": {"und": [{"value":  fullname, "format": None, "safe_value":  fullname}]},
                   'field_ckan_api_key': {'und': [{'value': apikey, "format": None, "safe_value": apikey}]}}
        headers = {"Content-type": "application/json", "X-CSRF-Token": token, "Cookie": cookie_header}
        r = requests.put(update_url, data=json.dumps(payload), headers=headers, verify=False)
        if r.status_code == requests.codes.ok:
            return True
        else:
            log.error("put " + update_url + " fails with http " + repr(r.status_code))
            log.error(repr(r.text))
            return False
    except Exception as e:
        log.error(e)
        return False


@side_effect_free
def action_user_show(context, data_dict):
    '''Modified from CKAN: user_show.

    Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary

    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id', None)
    provided_user = data_dict.get('user_obj', None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
        if user_obj is None:
            raise NotFound
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise NotFound

    toolkit.check_access('user_show', context, data_dict)

    user_dict = model_dictize.user_dictize(user_obj, context)
    user_dict = _add_user_extras(user_obj, user_dict)

    user_dict.pop('password', None)
    user_dict.pop('reset_key', None)

    keep_apikey = context.get('keep_apikey', False) or (context.get('for_view', False) and c.user == user_obj.name)
    keep_email = context.get('keep_email', False) or (context.get('for_view', False) and c.user == user_obj.name)
    if not keep_apikey:
        user_dict.pop('apikey', None)
    if not keep_email:
        user_dict.pop('email', None)
        user_dict.pop('email_hash', None)

    if context.get('return_minimal'):
        return user_dict

    revisions_q = model.Session.query(model.Revision).filter_by(author=user_obj.name)

    revisions_list = []
    for revision in revisions_q.limit(20).all():
        revision_dict = logic.get_action('revision_show')(context, {'id': revision.id})
        revision_dict['state'] = revision.state
        revisions_list.append(revision_dict)
    user_dict['activity'] = revisions_list

    user_dict['datasets'] = []
    dataset_q = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj, role=model.Role.ADMIN).limit(50)

    for dataset in dataset_q:
        try:
            dataset_dict = logic.get_action('package_show')(context, {'id': dataset.id})
        except logic.NotAuthorized:
            continue
        user_dict['datasets'].append(dataset_dict)

    user_dict['num_followers'] = logic.get_action('user_follower_count')({'model': model, 'session': model.Session}, {'id': user_dict['id']})

    return user_dict


@logic.auth_allow_anonymous_access
def auth_user_update(context, data_dict):
    """ Modified from CKAN: user_update """
    user = context['user']

    # FIXME: We shouldn't have to do a try ... except here, validation should
    # have ensured that the data_dict contains a valid user id before we get to
    # authorization.
    try:
        user_obj = auth.get_user_object(context, data_dict)
    except logic.NotFound:
        return {'success': False, 'msg': _('User not found')}

    if 'name' in data_dict and data_dict['name'] != user:
        return {'success': False, 'msg': _('Cannot change username')}
    if 'email' in data_dict and data_dict['email'] != user_obj.email:
        return {'success': False, 'msg': _('Cannot change email')}

    # If the user has a valid reset_key in the db, and that same reset key
    # has been posted in the data_dict, we allow the user to update
    # her account without using her password or API key.
    if user_obj.reset_key and 'reset_key' in data_dict:
        if user_obj.reset_key == data_dict['reset_key']:
            return {'success': True}

    if not user:
        return {'success': False,
                'msg': _('Have to be logged in to edit user')}

    if user == user_obj.name:
        # Allow users to update their own user accounts.
        return {'success': True}
    else:
        # Don't allow users to update other users' accounts.
        return {'success': False,
                'msg': _('User %s not authorized to edit user %s') %
                        (user, user_obj.id)}


def auth_user_list(context, data_dict):
    if not c.user:
        return {'success': False, 'msg': _('Have to be logged in to list users')}
    return {'success': True}


def auth_admin_list(context, data_dict):
    if not c.user:
        return {'success': False, 'msg': _('Have to be logged in to list admins')}
    return {'success': True}


def action_user_update(context, data_dict):
    ''' Modified from CKAN: user_update

    Update a user account.

    Normal users can only update their own user accounts. Sysadmins can update
    any user account.

    For further parameters see ``user_create()``.

    :param id: the name or id of the user to update
    :type id: string

    :returns: the updated user account
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']
    session = context['session']
    schema = context.get('schema') or logic.schema.default_update_user_schema()
    # Modify the schema by adding translation related keys
    add_translation_modify_schema(schema)

    upload = uploader.Upload('user')
    upload.update_data_dict(data_dict, 'image_url', 'image_upload', 'clear_upload')

    ignore_missing = toolkit.get_validator('ignore_missing')
    convert_to_extras = toolkit.get_converter('convert_to_extras')

    schema['job_title'] = [ignore_missing, unicode, convert_to_extras]
    schema['telephone_number'] = [ignore_missing, unicode, convert_to_extras]
    schema['main_organization'] = [ignore_missing, unicode, convert_to_extras]

    schema['image_url'] = [ignore_missing, unicode, convert_to_extras]

    schema['linkedin'] = [ignore_missing, unicode, convert_to_extras]
    schema['facebook'] = [ignore_missing, unicode, convert_to_extras]
    schema['twitter'] = [ignore_missing, unicode, convert_to_extras]

    schema['blog'] = [ignore_missing, to_list_json, convert_to_extras]
    schema['www_page'] = [ignore_missing, to_list_json, convert_to_extras]

    # Add the localized keys for the localized fields to the schema
    schema = add_languages_modify(schema, _localized_fields)

    not_empty = toolkit.get_validator('not_empty')
    schema['fullname'] = [not_empty, unicode]

    id = logic.get_or_bust(data_dict, 'id')

    user_obj = model.User.get(id)
    context['user_obj'] = user_obj
    if user_obj is None:
        raise NotFound('User was not found.')

    # If the translations are not in the data_dict, the user has not added any translations or the user has deleted all translations.
    # Therefore, the translations are not sent with the POST so we need to empty and update the translations here.
    if 'translations' not in data_dict:
        data_dict['translations'] = []

    toolkit.check_access('user_update', context, data_dict)

    data, errors = validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise ValidationError(errors)

    for extra in data['extras'] if 'extras' in data else []:
        user_obj.extras[extra['key']] = extra['value']

    user = model_save.user_dict_save(data, context)

    activity_dict = {'user_id': user.id,
                     'object_id': user.id,
                     'activity_type': 'changed user'}

    activity_create_context = {'model': model,
                               'user': user,
                               'defer_commit': True,
                               'ignore_auth': True,
                               'session': session}

    toolkit.get_action('activity_create')(activity_create_context, activity_dict)

    # Attempt to update drupal user
    _update_drupal_user(context, data_dict)

    # TODO: Also create an activity detail recording what exactly changed in
    # the user.

    upload.upload(uploader.get_max_image_size())
    if not context.get('defer_commit'):
        model.repo.commit()
    user_data = user_dictize(user, context)

    for key, value in user.extras.iteritems():
        if key in user_data:
            log.warning("Trying to override user data with extra variable '%s'", key)
            continue
        user_data[key] = value
    return user_data


@logic.side_effect_free
def action_user_list(context, data_dict):
    '''Return a list of the site's user accounts.
    :param q: restrict the users returned to those whose names contain a string
      (optional)
    :type q: string
    :param order_by: which field to sort the list by (optional, default:
      ``'name'``). Can be any user field or ``edits`` (i.e. number_of_edits).
    :type order_by: string
    :param all_fields: return full user dictionaries instead of just names.
      (optional, default: ``True``)
    :type all_fields: boolean
    :rtype: list of user dictionaries. User properties include:
      ``number_of_edits`` which counts the revisions by the user and
      ``number_created_packages`` which excludes datasets which are private
      or draft state.
    '''
    model = context['model']

    toolkit.check_access('user_list', context, data_dict)

    q = data_dict.get('q', '')
    order_by = data_dict.get('order_by', 'name')
    all_fields = asbool(data_dict.get('all_fields', True))

    if all_fields:
        query = model.Session.query(
            model.User,
            model.User.name.label('name'),
            model.User.fullname.label('fullname'),
            model.User.about.label('about'),
            model.User.about.label('email'),
            model.User.created.label('created'),
            _select([_func.count(model.Revision.id)],
                    _or_(
                        model.Revision.author == model.User.name,
                        model.Revision.author == model.User.openid
                    )).label('number_of_edits'),
            _select([_func.count(model.Package.id)],
                    _and_(
                        model.Package.creator_user_id == model.User.id,
                        model.Package.state == 'active',
                        model.Package.private == False,
                        )).label('number_created_packages')
        )
    else:
        query = model.Session.query(model.User.name)

    if q:
        query = model.User.search(q, query, user_name=context.get('user'))

    if order_by == 'edits':
        query = query.order_by(_desc(
            _select([_func.count(model.Revision.id)],
                    _or_(
                        model.Revision.author == model.User.name,
                        model.Revision.author == model.User.openid))))
    else:
        query = query.order_by(
            _case([(
                _or_(model.User.fullname == None,
                     model.User.fullname == ''),
                model.User.name)],
                else_=model.User.fullname))

    # Filter deleted users
    query = query.filter(model.User.state != model.State.DELETED)

    ## hack for pagination
    if context.get('return_query'):
        return query

    users_list = []

    if all_fields:
        for user in query.all():
            result_dict = model_dictize.user_dictize(user[0], context)
            result_dict.pop('email_hash', None)
            users_list.append(result_dict)

    else:
        for user in query.all():
            users_list.append(user[0])

    return users_list
