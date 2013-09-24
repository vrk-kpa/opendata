import logging

import ckan.plugins as p
import ckan.logic as logic
from ckanext.hierarchy.model import GroupTreeNode

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust


@logic.side_effect_free
def group_tree(context, data_dict):
    '''Returns the full group tree hierarchy.

    :returns: list of top-level GroupTreeNodes
    '''
    model = _get_or_bust(context, 'model')
    group_type = data_dict.get('type', 'group')
    return [_group_tree_branch(group, type=group_type)
            for group in model.Group.get_top_level_groups(type=group_type)]


@logic.side_effect_free
def group_tree_section(context, data_dict):
    '''Returns the section of the group tree hierarchy which includes the given
    group, from the top-level group downwards.

    :param id: the id or name of the group to inclue in the tree
    :returns: the top GroupTreeNode of the tree section
    '''
    group_name_or_id = _get_or_bust(data_dict, 'id')
    model = _get_or_bust(context, 'model')
    group = model.Group.get(group_name_or_id)
    if group is None:
        raise p.toolkit.ObjectNotFound
    group_type = data_dict.get('type', 'group')
    if group.type != group_type:
        how_type_was_set = 'was specified' if data_dict.get('type') \
                           else 'is filtered by default'
        raise p.toolkit.ValidationError(
            'Group type is "%s" not "%s" that %s' %
            (group.type, group_type, how_type_was_set))
    root_group = (group.get_parent_group_hierarchy(type=group_type) or [group])[0]
    return _group_tree_branch(root_group, highlight_group_name=group.name,
                              type=group_type)


def _group_tree_branch(root_group, highlight_group_name=None, type='group'):
    '''Returns a branch of the group tree hierarchy, rooted in the given group.

    :param root_group_id: group object at the top of the part of the tree
    :param highlight_group_name: group name that is to be flagged 'highlighted'
    :returns: the top GroupTreeNode of the tree
    '''
    nodes = {}  # group_id: GroupTreeNode()
    root_node = nodes[root_group.id] = GroupTreeNode(
        {'id': root_group.id,
         'name': root_group.name,
         'title': root_group.title})
    if root_group.name == highlight_group_name:
        nodes[root_group.id].highlight()
        highlight_group_name = None
    for group_id, group_name, group_title, parent_id in \
            root_group.get_children_group_hierarchy(type=type):
        node = GroupTreeNode({'id': group_id,
                              'name': group_name,
                              'title': group_title})
        nodes[parent_id].add_child_node(node)
        if highlight_group_name and group_name == highlight_group_name:
            node.highlight()
        nodes[group_id] = node
    return root_node
