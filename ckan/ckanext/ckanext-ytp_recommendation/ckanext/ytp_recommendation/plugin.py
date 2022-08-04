import ckan.plugins as plugins
from ckan.plugins import toolkit

from ckanext.ytp_recommendation import views, helpers, cli
from ckanext.ytp_recommendation.logic.action import create, get

log = __import__('logging').getLogger(__name__)


class Ytp_RecommendationPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'ytp_recommendation')

    def configure(self, config):
        # Raise an exception if required configs are missing
        required_keys = (
            'ckanext.ytp_recommendation.recaptcha_sitekey',
            'ckanext.ytp_recommendation.recaptcha_secret',
        )

        for key in required_keys:
            if config.get(key) is None:
                raise RuntimeError('Required configuration option {0} not found.'.format(key))

    # IActions
    def get_actions(self):
        return {
            'get_recommendation_count': get.get_recommendation_count_for_package,
            'create_recommendation': create.create_recommendation,
            'user_can_recommend': get.get_user_can_make_recommendation,
        }

    # IPackageController
    def before_view(self, pkg_dict):
        package_id = pkg_dict.get('id')
        data_dict = {'package_id': package_id}

        pkg_dict.update({
            'recommendation_count': self.get_actions().get('get_recommendation_count')({}, data_dict),
            'user_can_recommend': self.get_actions().get('user_can_recommend')({}, data_dict),
        })

        return pkg_dict

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_ytp_recommendation_recaptcha_sitekey': helpers.get_ytp_recommendation_recaptcha_sitekey,
        }

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # IClick

    def get_commands(self):
        return cli.get_commands()
