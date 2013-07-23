import ckan.plugins as p
import ckanext.hierarchy.lib.helpers as helpers

# This plugin is designed to work only these versions of CKAN
p.toolkit.check_ckan_version(min_version='2.0')

class OrganizationHierarchy(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IGroupForm, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        config['ckan.organization-hierarchy.enabled'] = True
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_template_directory(config, 'public')
        p.toolkit.add_resource('public/scripts/vendor/jstree', 'jstree')

    def before_map(self, map):
        # override the organization index route to use the group controller
        # instead of the organization controller, so that we can use a
        # custom index_template that extends the existing one (so can't
        # override the template.)
        map.connect('organizations_index', '/organization', controller='group', action='index')
        return map

    def index_template(self):
        return 'organization/hierarchy_index.html'

    def about_template(self):
        return 'organization/hierarchy_about.html'

    def setup_template_variables(self, context, data_dict):
        p.toolkit.c.tree = 'ff'
    
    def group_types(self):
        return ('organization',)

    def get_helpers(self):
        return {'group_tree': helpers.group_tree,
                'group_tree_branch': helpers.group_tree_branch}
