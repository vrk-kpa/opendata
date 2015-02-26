import ckan.plugins as plugins
from ckan.plugins import implements, toolkit


import logging

log = logging.getLogger(__name__)

class YtpCommentsPlugin(plugins.SingletonPlugin):
    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IPackageController, inherit=True)
    implements(plugins.ITemplateHelpers, inherit=True)

    # IConfigurer

    def configure(self, config):
        log.debug("Configuring comments module")


    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, 'public')


    def get_helpers(self):
        return {}

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
        return map
