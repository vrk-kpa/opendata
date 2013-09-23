import ckan.plugins as p
import ckanext.hierarchy.logic.action as action
from ckan.lib.plugins import DefaultGroupForm
from ckan.logic.validators import no_loops_in_hierarchy

# This plugin is designed to work only these versions of CKAN
p.toolkit.check_ckan_version(min_version='2.0')


class HierarchyDisplay(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IActions, inherit=True)

    # IConfigurer

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_template_directory(config, 'public')
        p.toolkit.add_resource('public/scripts/vendor/jstree', 'jstree')

    # IActions

    def get_actions(self):
        return {'group_tree': action.group_tree,
                'group_tree_section': action.group_tree_section,
                }


class HierarchyForm(p.SingletonPlugin, DefaultGroupForm):

    p.implements(p.IGroupForm, inherit=True)
        
    # IGroupForm

    def group_types(self):
        return ('organization',)

    def setup_template_variables(self, context, data_dict):
        from pylons import tmpl_context as c
        model = context['model']
        group_id = data_dict.get('id')
        if group_id:
            group = model.Group.get(group_id)
            c.allowable_parent_groups = \
                group.groups_allowed_to_be_its_parent(type='organization')
        else:
            c.allowable_parent_groups = model.Group.all(
                                                group_type='organization')

    def form_to_db_schema_options(self, options):
        schema = DefaultGroupForm.form_to_db_schema_options(self, options)
        # simple 'parent' field on the form needs converting to 'groups'
        schema['parent'] = [self._convert_parent_to_group]
        return schema

    @staticmethod
    def _convert_parent_to_group(key, data, errors, context):
        if ('parent',) in data:
            parent = data.get(('parent',))
            if ('groups',) not in data:
                data[('groups',)] = []
            data[('groups',)].append({'name': parent,
                                      'capacity': 'parent'})
            # need to check for loops here since 'groups' is already validated
            # at this point. Keys are tulples now, but the validator expects
            # strings.
            data_ = {'groups': data.get(('groups',))}
            if ('id',) in data:
                data_['id'] = data.get(('id',)) 
            no_loops_in_hierarchy(None, data_, None, context)

