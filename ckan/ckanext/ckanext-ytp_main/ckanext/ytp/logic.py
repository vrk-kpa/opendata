from ckan import logic
from ckan.common import _, c
from ckan.logic import auth, check_access
from ckan.model import Package
from ckan.lib.mailer import mail_recipient, MailerException
import ckan.authz as authz
import ckan.lib.plugins as lib_plugins
import ckan.lib.search as search
import ckan.model as model
from ckan.plugins import toolkit
from ckanext.dcat.logic import _pagination_info, DATASETS_PER_PAGE, wrong_page_exception
from dateutil.parser import parse as dateutil_parse
from ckanext.ytp.dcat import AvoindataSerializer

import logging
import sqlalchemy
import sqlalchemy.sql

from .model import MunicipalityBoundingBox

_select = sqlalchemy.sql.select
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_check_access = check_access

log = logging.getLogger(__name__)


# Insert here the fields that are localized
_localized_fields = ['job_title', 'about']


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


def send_package_deprecation_emails(packages):
    grouped_by_maintainer = {}
    for package in packages:
        fullPackage = Package.get(package)
        maintainer_email = fullPackage.maintainer_email

        packageInfoForEmail = {
            "title": fullPackage.title,
            "id": fullPackage.id,
            "valid_till": fullPackage.extras.get("valid_till"),
        }

        if maintainer_email not in grouped_by_maintainer:
            grouped_by_maintainer[maintainer_email] = {"maintainer": fullPackage.maintainer, "packages": [packageInfoForEmail]}
        else:
            grouped_by_maintainer[maintainer_email]["packages"].append(packageInfoForEmail)

    for maintainer_email, details in grouped_by_maintainer.items():
        send_deprecation_email_user(
            maintainer_email,
            details["packages"],
            details["maintainer"],
            details["packages"][0]["valid_till"]
        )


def send_deprecation_email_user(maintainer_email, packages, maintainer, valid_till):
    from .email_templates import deprecation_email_user
    log.info('send deprecation email user')
    subject = deprecation_email_user.subject.format(valid_till=valid_till)
    body = deprecation_email_user.messageBody(maintainer, packages)
    try:
        mail_recipient(maintainer, maintainer_email, subject, body)
    except MailerException as e:
        log.error(e)


def package_autocomplete(context, data_dict):
    '''Return a list of datasets (packages) that match a string.
    Datasets with names or titles that contain the query string will be
    returned.
    :param q: the string to search for
    :type q: string
    :param limit: the maximum number of resource formats to return (optional,
        default: ``10``)
    :type limit: int
    :param package_type: the dataset type to filter based on (optional)
    :type package_type: string
    :rtype: list of dictionaries
    '''
    _check_access('package_autocomplete', context, data_dict)
    user = context.get('user')

    limit = data_dict.get('limit', 10)
    q = data_dict['q']
    package_type = data_dict.get('package_type', None)

    # enforce permission filter based on user
    if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
        labels = None
    else:
        labels = lib_plugins.get_permission_labels().get_user_dataset_labels(
            context['auth_user_obj']
        )

    if package_type:
        # Only show datasets of this particular type
        fq = ' +dataset_type:{type}'.format(type=package_type)

    data_dict = {
        'q': ' OR '.join([
            'name_ngram:{0}',
            'title_ngram:{0}',
            'name:{0}',
            'title:{0}',
        ]).format(search.query.solr_literal(q)),
        'fq': fq.strip(),
        'fl': 'name,title',
        'rows': limit
    }
    query = search.query_for(model.Package)

    results = query.run(data_dict, permission_labels=labels)['results']

    q_lower = q.lower()
    pkg_list = []
    for package in results:
        if q_lower in package['name']:
            match_field = 'name'
            match_displayed = package['name']
        else:
            match_field = 'title'
            match_displayed = '%s (%s)' % (package['title'], package['name'])
        result_dict = {
            'name': package['name'],
            'title': package['title'],
            'match_field': match_field,
            'match_displayed': match_displayed}
        pkg_list.append(result_dict)

    return pkg_list


def store_municipality_bbox_data(context, data_dict):
    objects = []
    bbox_data = data_dict.get(u'bbox_data')

    for k, v in bbox_data.items():
        assert len(v) == 4
        v.sort(key=float)  # Sort to ensure correct order of coordinates
        objects.append(
            MunicipalityBoundingBox(
                name=k,
                lat_max=v[3],
                lat_min=v[2],
                lng_max=v[1],
                lng_min=v[0]
            )
        )

    MunicipalityBoundingBox.bulk_save(objects)


# Copied from https://github.com/ckan/ckanext-dcat/blob/v1.3.0/ckanext/dcat/logic.py#L35 with minor modifications
@toolkit.chained_action
@toolkit.side_effect_free
def dcat_catalog_show(original_action, context, data_dict):
    toolkit.check_access('dcat_catalog_show', context, data_dict)

    fq = data_dict.get('fq', '')

    if fq:
        fq += ' AND (dataset_type:dataset OR dataset_type:apiset OR dataset_type:showcase)'
    else:
        fq = '(dataset_type:dataset OR dataset_type:apiset OR dataset_type:showcase)'
    
    data_dict['fq'] = fq
    
    query = _search_ckan_datasets(context, data_dict)
    dataset_dicts = query['results']
    pagination_info = _pagination_info(query, data_dict)

    serializer = AvoindataSerializer(profiles=data_dict.get('profiles'))

    output = serializer.serialize_catalog({}, dataset_dicts,
                                          _format=data_dict.get('format'),
                                          pagination_info=pagination_info)

    return output


def _search_ckan_datasets(context, data_dict):

    n = int(toolkit.config.get('ckanext.dcat.datasets_per_page', DATASETS_PER_PAGE))
    page = data_dict.get('page', 1) or 1

    try:
        page = int(page)
        if page < 1:
            raise wrong_page_exception
    except ValueError:
        raise wrong_page_exception

    modified_since = data_dict.get('modified_since')
    if modified_since:
        try:
            modified_since = dateutil_parse(modified_since).isoformat() + 'Z'
        except (ValueError, AttributeError):
            raise toolkit.ValidationError(
                'Wrong modified date format. Use ISO-8601 format')

    search_data_dict = {
        'rows': n,
        'start': n * (page - 1),
        'sort': 'metadata_modified desc',
    }

    search_data_dict['q'] = data_dict.get('q', '*:*')
    search_data_dict['fq'] = data_dict.get('fq')
    search_data_dict['fq_list'] = []

    # Exclude certain dataset types
    search_data_dict['fq_list'].append('-dataset_type:harvest')

    if modified_since:
        search_data_dict['fq_list'].append(
            'metadata_modified:[{0} TO NOW]'.format(modified_since))

    query = toolkit.get_action('package_search')(context, search_data_dict)

    return query
