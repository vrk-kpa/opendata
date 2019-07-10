import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class AdvancedsearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'advancedsearch')

    def before_map(self, m):
        m.connect(
            '/advanced_search',
            action='search',
            controller='ckanext.advancedsearch.controller:YtpAdvancedSearchController'
        )
        return m
