import ckan.plugins as plugins

import logging

log = logging.getLogger(__name__)

class YtpCommentsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def configure(self, config):
        log.debug("Configuring comments module")
        

    def update_config(self, config):
        plugins.toolkit._add_template_directory(config, "templates")

    # IPackageController

    def before_view(self, pkg_dict):
        # TODO: append comments from model to pkg_dict
        return  pkg_dict

    # IRoutes

    def before_map(self, map):
        # TODO: add route for adding comment
        return map
