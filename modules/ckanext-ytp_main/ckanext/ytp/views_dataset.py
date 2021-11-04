# encoding: utf-8
import logging
from collections import OrderedDict
from functools import partial
from six.moves.urllib.parse import urlencode
from datetime import datetime
from ckan.plugins import toolkit

from flask import Blueprint
from flask.views import MethodView
from werkzeug.datastructures import MultiDict
from ckan.common import asbool
from ckan.views import dataset as dataset_views

import six
from six import string_types, text_type
import re
import urllib2
import urllib

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as plugins
import ckan.authz as authz
from ckan.common import _, config, g, request, response
from ckan.views.home import CACHE_PARAMETERS
from ckan.lib.plugins import lookup_package_plugin
from ckan.lib.render import TemplateNotFound
from ckan.lib.search import SearchError, SearchQueryError, SearchIndexError
from ckan.views import LazyView


NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
_tag_string_to_list = dataset_views._tag_string_to_list
_form_save_redirect = dataset_views._form_save_redirect
_setup_template_variables = dataset_views._setup_template_variables
_get_pkg_template = dataset_views._get_pkg_template

log = logging.getLogger(__name__)

def create_vocabulary(name, defer=False):
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    try:
        data = {'id': name}
        return toolkit.get_action('vocabulary_show')(context, data)
    except NotFound:
        pass

    log.info("Creating vocab '" + name + "'")
    data = {'name': name}
    try:
        if defer:
            context['defer_commit'] = True
        return toolkit.get_action('vocabulary_create')(context, data)
    except Exception as e:
        log.error('%s' % e)

def ytp_tag_autocomplete():
    """ CKAN autocomplete discards vocabulary_id from request.
        This is modification from tag_autocomplete function from CKAN.
        Takes vocabulary_id as parameter.
    """
    q = request.params.get('incomplete', '')
    limit = request.params.get('limit', 10)
    vocabulary_id = request.params.get('vocabulary_id', None)
    if vocabulary_id:
        create_vocabulary(vocabulary_id)

    tag_names = []
    if q:
        context = {'model': model, 'session': model.Session, 'user': g.user or g.author}
        data_dict = {'q': q, 'limit': limit}
        if vocabulary_id:
            data_dict['vocabulary_id'] = vocabulary_id
        try:
            tag_names = get_action('tag_autocomplete')(context, data_dict)
        except NotFound:
            pass  # return empty when vocabulary is not found
    resultSet = {
        'ResultSet': {
            'Result': [{'Name': tag} for tag in tag_names]
        }
    }

    status_int = 200
    response.status_int = status_int
    response.headers['Content-Type'] = 'application/json;charset=utf-8'
    return h.json.dumps(resultSet)


def new_metadata(id, data=None, errors=None, error_summary=None):
    """ Fake metadata creation. Change status to active and redirect to read. """
    context = {'model': model, 'session': model.Session,
                'user': g.user or g.author, 'auth_user_obj': g.userobj}

    data_dict = get_action('package_show')(context, {'id': id})
    data_dict['id'] = id
    data_dict['state'] = 'active'
    context['allow_state_change'] = True

    get_action('package_update')(context, data_dict)
    success_message = ('<div style="display: inline-block"><p>' + _("Dataset was saved successfully.") + '</p>' +
                        '<p>' + _("Fill additional info") + ':</p>' +
                        '<p><a href="/data/' + h.lang() + '/dataset/' + data_dict.get('name') + '/related/new">>'
                        + _("Add related") + '</a></p>' +
                        '<p><a href="/data/' + h.lang() + '/dataset/edit/' + data_dict.get('name') + '">>'
                        + _("Edit or add language versions") + '</a> ' +
                        '<a href="/data/' + h.lang() + '/dataset/delete/' + id + '">>' + _('Delete') + '</a></p>' +
                        '<p><a href="/data/' + h.lang() + '/dataset/new/">' + _('Create Dataset') + '</a></p></div>')
    h.flash_success(success_message, True)
    h.redirect_to(controller='ytp_dataset_blueprint', action='read', id=id)


def healthcheck():
    SITE_URL_FAILURE_LOGMESSAGE = "Site URL '%s' failed to respond during health check."
    FAILURE_MESSAGE = "An error has occurred, check the server log for details"
    SUCCESS_MESSAGE = "OK"
    check_site_urls = ['/fi', '/data/fi/dataset']


    def check_url(host, url):
        try:
            req = urllib2.Request('http://localhost%s' % url)
            req.add_header('Host', host)
            response = urllib2.urlopen(req, timeout=30)
            return response.getcode() == 200
        except urllib2.URLError:
            return False
    result = True
    site_url = config.get('ckan.site_url')
    host = re.sub(r'https?:\/\/', '', site_url)

    for url in check_site_urls:
        if not check_url(host, url):
            log.warn(SITE_URL_FAILURE_LOGMESSAGE % url)
            result = False

    if result:
        base.abort(200, SUCCESS_MESSAGE)
    else:
        base.abort(503, FAILURE_MESSAGE)


healthcheck_blueprints = Blueprint(
    u'ytp_healthcheck',
    __name__
)
healthcheck_blueprints.add_url_rule(u'/health', view_func=healthcheck)

api_blueprints = Blueprint(
    u'ytp_api_blueprints',
    __name__,
    url_prefix=u'/api'
)
api_blueprints.add_url_rule(u'/2/util/tag/autocomplete', view_func=ytp_tag_autocomplete)
# NOTE: Is dataset_autocomplete deprecated as there was no function for that in package-controller or ytpDatasetController
# api_blueprints.add_url_rule(u'/util/dataset/autocomplete', view_func=dataset_autocomplete)

dataset = Blueprint(
    u'ytp_dataset_blueprint',
    __name__,
    url_prefix=u'/dataset',
    url_defaults={u'package_type': u'dataset'}
)
dataset.add_url_rule(u'/', view_func=dataset_views.search, strict_slashes=False)
dataset.add_url_rule(u'/new_metadata/<id>', view_func=new_metadata)
dataset.add_url_rule(u'/new', view_func=dataset_views.CreateView.as_view(str(u'new')))
dataset.add_url_rule(u'/resources/<id>', view_func=dataset_views.resources)
dataset.add_url_rule(
    u'/edit/<id>', view_func=dataset_views.EditView.as_view(str(u'edit'))
)
dataset.add_url_rule(
    u'/delete/<id>', view_func=dataset_views.DeleteView.as_view(str(u'delete'))
)
dataset.add_url_rule(
    u'/follow/<id>', view_func=dataset_views.follow, methods=(u'POST', )
)
dataset.add_url_rule(
    u'/unfollow/<id>', view_func=dataset_views.unfollow, methods=(u'POST', )
)
dataset.add_url_rule(u'/followers/<id>', view_func=dataset_views.followers)
dataset.add_url_rule(
    u'/groups/<id>', view_func=dataset_views.GroupView.as_view(str(u'groups'))
)
dataset.add_url_rule(u'/activity/<id>', view_func=dataset_views.activity)
dataset.add_url_rule(u'/changes/<id>', view_func=dataset_views.changes)
dataset.add_url_rule(u'/<id>/history', view_func=dataset_views.history)

dataset.add_url_rule(u'/changes_multiple', view_func=dataset_views.changes_multiple)

# Duplicate resource create and edit for backward compatibility. Note,
# we cannot use resource.CreateView directly here, because of
# circular imports
dataset.add_url_rule(
    u'/new_resource/<id>',
    view_func=LazyView(
        u'ckan.views.resource.CreateView', str(u'new_resource')
    ),
    endpoint=u'new_resource'
)

dataset.add_url_rule(
    u'/<id>/resource_edit/<resource_id>',
    view_func=LazyView(
        u'ckan.views.resource.EditView', str(u'edit_resource')
    ),
    endpoint=u'edit_resource'
)

if authz.check_config_permission(u'allow_dataset_collaborators'):
    dataset.add_url_rule(
        rule=u'/collaborators/<id>',
        view_func=dataset_views.collaborators_read,
        methods=['GET', ]
    )

    dataset.add_url_rule(
        rule=u'/collaborators/<id>/new',
        view_func=dataset_views.CollaboratorEditView.as_view(str(u'new_collaborator')),
        methods=[u'GET', u'POST', ]
    )

    dataset.add_url_rule(
        rule=u'/collaborators/<id>/delete/<user_id>',
        view_func=dataset_views.collaborator_delete, methods=['POST', ]
    )
dataset.add_url_rule(u'/<id>', view_func=dataset_views.read)

def get_blueprints():
    return [dataset, healthcheck_blueprints]