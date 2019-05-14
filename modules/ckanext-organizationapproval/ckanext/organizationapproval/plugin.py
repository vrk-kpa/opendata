import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class OrganizationApprovalPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_ckan_admin_tab(config_, 'manage_organizations', 'Manage organizations')

    # IRoutes
    def before_map(self, map):
        organization_controller = 'ckanext.organizationapproval.controller:OrganizationApprovalController'

        map.connect('manage_organizations',
                    '/ckan-admin/organization_management',
                    controller=organization_controller,
                    action='manage_organizations',
                    ckan_icon='picture')

        return map
