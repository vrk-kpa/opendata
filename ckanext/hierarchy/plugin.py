import ckan.plugins as p
import ckanext.hierarchy.lib.helpers as helpers
import ckanext.hierarchy.logic.action as action

# This plugin is designed to work only these versions of CKAN
p.toolkit.check_ckan_version(min_version='2.0')

class OrganizationHierarchy(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IGroupForm, inherit=True)
    p.implements(p.IActions, inherit=True)

    # IConfigurer

    def update_config(self, config):
        config['ckan.organization-hierarchy.enabled'] = True
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_template_directory(config, 'public')
        p.toolkit.add_resource('public/scripts/vendor/jstree', 'jstree')

    # IGroupForm

    def group_types(self):
        return ('organization',)

    # IActions

    def get_actions(self):
        return {'group_tree': action.group_tree,
                'group_tree_section': action.group_tree_section,
                }
