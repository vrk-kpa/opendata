from ckan import plugins
from ckan.plugins import toolkit
import sqlalchemy
from ckan.common import c
from ckan import model
from ckan.logic import NotFound
from ckan.lib import helpers
from ckan.lib.plugins import DefaultTranslation

from flask import request, Blueprint
import requests
import urllib
import uuid

import logging
log = logging.getLogger(__name__)


def user_delete_me(context, data_dict):
    if not c.userobj:
        return {'success': False}
    return {'success': True}


def delete_me(self):
    try:
        if not c.userobj:
            raise toolkit.NotAuthorized

        if request.params.get('delete', None) != 'true':
            return toolkit. render('user/delete_me.html')

        from ckan.lib.celery_app import celery
        context = {'model': model, 'session': model.Session, 'user': c.user}
        toolkit.check_access('user_delete_me', context, {})

        celery.send_task("ckanext.ytp_drupal.delete_user", args=(c.userobj.id,), task_id=str(uuid.uuid4()))
        toolkit.redirect(toolkit.get_plugin('ytp_drupal').cancel_url)
    except toolkit.NotAuthorized:
        msg = toolkit._('Unauthorized to delete user')
        toolkit.abort(401, msg.format(user_id=id))


class YtpDrupalPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)

    _config_template = "ckanext.ytp.drupal.%s"
    _node_type = 'service_alert'
    _node_status = '1'  # published content has status 1, unpublised has status 0
    _language_fallback_order = ['fi', 'en', 'sv']
    cancel_url = None

    def get_blueprint(self):
        bp = Blueprint('ytp_drupal', __name__)
        bp.add_url_rule('/user/delete-me', endpoint='user_delete_me', view_func=delete_me)
        return bp

    def configure(self, config):
        connection_variable = self._config_template % "connection"
        self.drupal_connection_url = config.get(connection_variable)
        if not self.drupal_connection_url:
            raise Exception('YtpDrupalPlugin: required configuration variable missing: %s' % (connection_variable))

        self.cancel_url = config.get(self._config_template % "cancel_url", "/cancel-user.php")
        self._node_type = config.get(self._config_template % "node_type", self._node_type)
        self._translations_disabled = toolkit.asbool(config.get(self._config_template % "translations_disabled", "false"))

        self.engine = sqlalchemy.create_engine(self.drupal_connection_url)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def _service_alerts(self):
        """ Get service alerts from Drupal """
        language = None if self._translations_disabled else helpers.lang()
        return self.engine.execute("""SELECT nid, title FROM node WHERE type = %(type)s AND
                                      language = %(language)s AND status = %(status)s""",
                                   {'type': self._node_type, 'language': language, 'status': self._node_status})

    def _fetch_drupal_content(self, identifier, language=None, fallback=True):
        """ This helper fetches content from Drupal database using url alias identifier.
            Return content as dictionary containing language, title, body, node_id and edit link. None if not found.
            Tries to fallback to different language if fallback is True.

            Not cached.
        """
        if not language:
            language = helpers.lang()

        query = """SELECT url_alias.language, node.title, field_revision_body.body_value, node.nid from url_alias
                       INNER JOIN node ON node.nid = split_part(url_alias.source, '/', 2)::integer
                       INNER JOIN field_revision_body ON field_revision_body.entity_id = split_part(url_alias.source, '/', 2)::integer
                   WHERE url_alias.alias = %(identifier)s"""  # noqa: E501

        results = {}
        for content_language, title, body, node_id in self.engine.execute(query, {'identifier': identifier}):
            results[content_language] = {'language': content_language, 'title': title, 'body': body, 'node_id': node_id}

        result = results.get(language, None)

        if not result and fallback and results:
            for fallback_language in self._language_fallback_order:
                result = results.get(fallback_language)
                if result:
                    break
            if not result:
                result = next(iter(results.values()))

        if result:
            result['edit'] = urllib.parse.quote("/%s/node/%s/edit" % (language, str(result['node_id'])))
            result['body'] = toolkit.h.literal(result['body'])

        return result

    def get_drupal_user_id(self, username):
        result = self.engine.execute("SELECT uid FROM users_field_data WHERE name = %(name)s", {'name': username})
        for row in result:
            return row[0]
        raise NotFound

    def get_drupal_session_cookie(self):
        '''returns tuple of (cookie_name, cookie_value)'''
        request_cookies = request.cookies
        session_cookie = None
        for cookie_key in request_cookies:
            if cookie_key[:5] == 'SSESS':
                session_cookie = (cookie_key, request_cookies[cookie_key])
        return session_cookie

    def get_drupal_session_token(self, domain, service, cookie_header=''):
        '''return text of X-CSRF-Token)'''
        token_url = 'https://' + domain + '/' + service + '/?q=services/session/token'
        verify_cert = plugins.toolkit.config.get('ckanext.drupal8.development_cert', '') or True
        token_request = requests.get(token_url, headers={"Cookie": cookie_header}, verify=verify_cert)
        token = token_request.text
        return token

    def get_helpers(self):
        return {'service_alerts': self._service_alerts, 'fetch_drupal_content': self._fetch_drupal_content}

    def get_auth_functions(self):
        return {'user_delete_me': user_delete_me}
