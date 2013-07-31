import logging

import ckan.plugins as p
import ckan.logic as logic
from ckanext.hierarchy.model import GroupTreeNode, group_dictize

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
    return _group_tree_branch(root_group, highlight_group=group,
                              type=group_type)


def _group_tree_branch(root_group, highlight_group=None, type='group'):
    '''Returns a branch of the group tree hierarchy, rooted in the given group.

    :param root_group: group object at the top of the part of the tree
    :param highlight_group: group object that is to be flagged 'highlighted'
    :returns: the top GroupTreeNode of the tree
    '''
    nodes = {}  # group_id: GroupTreeNode()
    root_node = nodes[root_group.id] = GroupTreeNode(group_dictize(root_group))
    if root_group == highlight_group:
        nodes[root_group.id].highlight()
        highlight_group = None
    elif highlight_group:
        highlight_group_id = highlight_group.id
    for group, parent_id in root_group.get_children_group_hierarchy(type=type):
        nodes[group.id] = GroupTreeNode(group_dictize(group))
        nodes[parent_id].add_child_node(nodes[group.id])
        if highlight_group and group.id == highlight_group_id:
            nodes[group.id].highlight()
    return root_node
