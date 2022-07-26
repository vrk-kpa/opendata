from ckan import plugins
from ckanext.ytp_tasks import logic
from .cli import get_commands


class YtpTasksPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IClick)

    def configure(self, config):
        pass

    def get_actions(self):
        return {'ytp_tasks_add': logic.action_ytp_tasks_add}

    def get_auth_functions(self):
        return {'ytp_tasks_add': logic.auth_ytp_tasks_add}

    def get_commands(self):
        return get_commands()
