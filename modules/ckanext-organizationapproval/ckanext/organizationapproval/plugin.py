import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class OrganizationApprovalPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    # # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_ckan_admin_tab(config_, 'manage_organizations', 'Manage organizations')

    # # IRoutes
    def before_map(self, map):
        organization_approval_controller = 'ckanext.ytp.controller:OrganizationApprovalController'

        map.connect('/organization/new', action='new', controller=organization_approval_controller)
