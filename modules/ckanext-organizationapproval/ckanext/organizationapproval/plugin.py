import sys
import os
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from helpers import make_pager_url


class OrganizationApprovalPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)

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

    def get_helpers(self):
        return {'make_pager_url': make_pager_url}

    # ITranslator

    # The following methods are copied from ckan.lib.plugins.DefaultTranslation
    # and have been modified to fix a bug in CKAN 2.5.1 that prevents CKAN from
    # starting. In addition by copying these methods, it is ensured that Data
    # Requests can be used even if Itranslation isn't available (less than 2.5)

    def i18n_directory(self):
        '''Change the directory of the *.mo translation files
        The default implementation assumes the plugin is
        ckanext/myplugin/plugin.py and the translations are stored in
        i18n/
        '''
        # assume plugin is called ckanext.<myplugin>.<...>.PluginClass
        extension_module_name = '.'.join(self.__module__.split('.')[:3])
        module = sys.modules[extension_module_name]
        return os.path.join(os.path.dirname(module.__file__), 'i18n')

    def i18n_locales(self):
        '''Change the list of locales that this plugin handles
        By default the will assume any directory in subdirectory in the
        directory defined by self.directory() is a locale handled by this
        plugin
        '''
        directory = self.i18n_directory()
        return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    def i18n_domain(self):
        '''Change the gettext domain handled by this plugin
        This implementation assumes the gettext domain is
        ckanext-{extension name}, hence your pot, po and mo files should be
        named ckanext-{extension name}.mo'''
        return 'ckanext-{name}'.format(name=self.name)
