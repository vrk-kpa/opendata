import logging
import ckan.plugins as p
import ckan.logic as logic
from ckanext.ytp.organizations.model import GroupTreeNode
from ckan import model

log = logging.getLogger(__name__)


def _fetch_all_organizations():
    groups = model.Session.query(model.Group) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .all()
    members = model.Session.query(model.Member) \
        .join(model.Group, model.Member.table_id == model.Group.id) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .all()
    extras = model.Session.query(model.GroupExtra.group_id, model.GroupExtra.key, model.GroupExtra.value) \
        .join(model.Group, model.GroupExtra.group_id == model.Group.id) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .all()

    groups_by_id = {g.id: g for g in groups}
    parent_ids = {m.group_id for m in members}
    child_ids = {m.table_id for m in members}
    extras_by_group = {}
    for group_id, key, value in extras:
        group_extras = extras_by_group.get(group_id, {})
        group_extras[key] = value
        extras_by_group[group_id] = group_extras

    # Set extras-dicts into a custom version of extras to avoid triggering SQLAlchemy queries
    for group in groups:
        group.custom_extras = extras_by_group.get(group.id, {})

    parent_child_id_map = {pid: [m.table_id for m in members if m.group_id == pid] for pid in parent_ids}

    def group_children(gid):
        for child_id in parent_child_id_map.get(gid, []):
            child = groups_by_id[child_id]
            yield (child.id, child.name, child.title, gid, child.custom_extras)

    children = {g.id: [c for c in group_children(g.id)] for g in groups}
    roots = [g for g in groups if g.id not in child_ids]

    return roots, children


@logic.side_effect_free
def group_tree(context, data_dict):
    '''Returns the full group tree hierarchy.

    :returns: list of top-level GroupTreeNodes
    '''
    top_level_groups, children = _fetch_all_organizations()
    group_type = data_dict.get('type', 'group')
    sorted_top_level_groups = sorted(top_level_groups, key=lambda g: g.name)
    result = [_group_tree_branch(group, type=group_type, children=children.get(group.id, []))
              for group in sorted_top_level_groups]
    return result


@logic.side_effect_free
def group_tree_section(context, data_dict):
    '''Returns the section of the group tree hierarchy which includes the given
    group, from the top-level group downwards.

    :param id: the id or name of the group to inclue in the tree
    :returns: the top GroupTreeNode of the tree section
    '''
    group = model.Group.get(data_dict['id'])
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


def _group_tree_branch(root_group, highlight_group_name=None, type='group', children=[]):
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

    root_node.update(root_group.custom_extras)
    if root_group.name == highlight_group_name:
        nodes[root_group.id].highlight()
        highlight_group_name = None

    sorted_children = sorted(children, key=lambda c: c[1])
    for group_id, group_name, group_title, parent_id, extras in sorted_children:
        node = GroupTreeNode({'id': group_id,
                              'name': group_name,
                              'title': group_title})
        if extras:
            node.update(extras)
        nodes[parent_id].add_child_node(node)
        if highlight_group_name and group_name == highlight_group_name:
            node.highlight()
        nodes[group_id] = node
    return root_node
