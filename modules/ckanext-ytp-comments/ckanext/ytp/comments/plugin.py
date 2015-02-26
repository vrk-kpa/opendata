import ckan.plugins as plugins
from ckan.plugins import implements, toolkit


import logging

log = logging.getLogger(__name__)

class YtpCommentsPlugin(plugins.SingletonPlugin):
    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IPackageController, inherit=True)
    implements(plugins.ITemplateHelpers, inherit=True)
    implements(plugins.IActions, inherit=True)

    # IConfigurer

    def configure(self, config):
        log.debug("Configuring comments module")


    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, 'public')


    def get_helpers(self):
        return {}

    def get_actions(self):
        import ckanext.ytp.comments.logic.action as actions
        return {
            "comment_create": actions.create.comment_create
        }
    # IPackageController

    def before_view(self, pkg_dict):
        # TODO: append comments from model to pkg_dict
        return  pkg_dict

    # IRoutes

    def before_map(self, map):
        """
            /dataset/NAME/comments/reply/PARENT_ID
            /dataset/NAME/comments/add
        """
        controller = 'ckanext.ytp.comments.controller:CommentController'
        map.connect('/dataset/{dataset_name}/comments/add', controller=controller, action='add')
        return map
