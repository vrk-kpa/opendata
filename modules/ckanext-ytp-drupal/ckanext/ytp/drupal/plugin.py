from ckan import plugins
from ckan.plugins import toolkit
from paste.deploy.converters import asbool
import sqlalchemy
from ckan.common import c
from ckan.logic import NotFound


def user_delete_me(context, data_dict):
    if not c.userobj:
        return {'success': False}
    return {'success': True}


class YtpDrupalPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    _config_template = "ckanext.ytp.drupal.%s"
    _node_type = 'service_alert'
    cancel_url = None

    def before_map(self, m):
        """ Override delete page """
        controller = 'ckanext.ytp.drupal.controller:YtpDrupalController'
        m.connect('user_delete_me', '/user/delete-me', action='delete_me', controller=controller)
        return m

    def configure(self, config):
        connection_variable = self._config_template % "connection"
        self.drupal_connection_url = config.get(connection_variable)
        if not self.drupal_connection_url:
            raise Exception('YtpDrupalPlugin: required configuration variable missing: %s' % (connection_variable))

        self.cancel_url = config.get(self._config_template % "cancel_url", "/cancel-user.php")
        self._node_type = config.get(self._config_template % "node_type", self._node_type)
        self._translations_disabled = asbool(config.get(self._config_template % "translations_disabled", "false"))

        self.engine = sqlalchemy.create_engine(self.drupal_connection_url)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def _request_language(self):
        return toolkit.request.environ.get('CKAN_LANG')

    def _service_alerts(self):
        language = None if self._translations_disabled else self._request_language()
        return self.engine.execute("""SELECT nid, title FROM node WHERE type = %(type)s AND language = %(language)s""",
                                   {'type': self._node_type, 'language': language})

    def get_drupal_user_id(self, username):
        result = self.engine.execute("SELECT uid FROM users WHERE name = %(name)s", {'name': username})
        for row in result:
            return row[0]
        raise NotFound

    def get_helpers(self):
        return {'service_alerts': self._service_alerts}

    def get_auth_functions(self):
        return {'user_delete_me': user_delete_me}
