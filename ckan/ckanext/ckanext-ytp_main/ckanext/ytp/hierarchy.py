import logging
import ckan.plugins as p
import ckan.logic as logic
from ckanext.hierarchy.model import GroupTreeNode
from ckan import model
from ckan.authz import is_sysadmin
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased

log = logging.getLogger(__name__)


def _accumulate_dataset_counts(groups, members):
    members_by_group = {}
    for m in members:
        members_by_group.setdefault(m.group_id, []).append(m.table_id)

    dataset_count_map = {g.id: 0 for g in groups}
    child_parents_map = {gid: members_by_group.get(gid, []) for gid in dataset_count_map.keys()}

    def add_to_ancestors(id, value, counts):
        if id in counts:
            counts[id] += value
            parents = child_parents_map.get(id, [])
            if parents:
                for parent in parents:
                    add_to_ancestors(parent, value, counts)

    for group in groups:
        if group.dataset_count:
            add_to_ancestors(group.id, group.dataset_count, dataset_count_map)

    return dataset_count_map


def _fetch_all_organizations(user=None, force_root_ids=None, only_approved=False):
    log.info(f'only_approved: {only_approved}')
    if is_sysadmin(user) and not only_approved:
        non_approved = []
    else:
        # Find names of all non-approved organizations
        query = (model.Session.query(model.Group.name)
                 .filter(model.Group.state == u'active')
                 .filter(model.Group.approval_status != u'approved'))

        non_approved = set(result[0] for result in query.all())

        # If user is logged in, retain only names of organizations the user is not a member of
        if user and not only_approved:
            query = (model.Session.query(model.Group.name)
                     .join(model.Member, model.Member.group_id == model.Group.id)
                     .join(model.User, model.User.id == model.Member.table_id)
                     .filter(model.Member.state == u'active')
                     .filter(model.Member.table_name == u'user')
                     .filter(model.User.name == user)
                     .filter(model.Group.state == u'active')
                     .filter(model.Group.approval_status != u'approved'))
            memberships = set(result[0] for result in query.all())
            non_approved -= memberships

    groups_with_counts = model.Session.query(model.Group, func.count(model.Package.id)) \
        .outerjoin(model.Package, and_(model.Package.owner_org == model.Group.id, model.Package.state == u'active')) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .filter(model.Group.name.notin_(non_approved)) \
        .group_by(model.Group.id) \
        .all()  # noqa

    parent_group = aliased(model.Group)
    members = model.Session.query(model.Member) \
        .join(model.Group, model.Member.table_id == model.Group.id) \
        .join(parent_group, model.Member.group_id == parent_group.id) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .filter(model.Member.table_name == u'group') \
        .filter(model.Member.state == u'active')\
        .filter(parent_group.state == u'active') \
        .filter(parent_group.is_organization.is_(True)) \
        .all()

    extras = model.Session.query(model.GroupExtra.group_id, model.GroupExtra.key, model.GroupExtra.value) \
        .join(model.Group, model.GroupExtra.group_id == model.Group.id) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .filter(model.GroupExtra.state == u'active')\
        .all()

    groups = []
    for group, count in groups_with_counts:
        group.dataset_count = count
        groups.append(group)

    groups_by_id = {g.id: g for g in groups}
    parent_ids = {m.table_id for m in members}
    child_ids = {m.group_id for m in members}
    extras_by_group = {}
    for group_id, key, value in extras:
        group_extras = extras_by_group.get(group_id, {})
        group_extras[key] = value
        extras_by_group[group_id] = group_extras

    dataset_counts = _accumulate_dataset_counts(groups, members)

    for gid, group in groups_by_id.items():
        # Set extras-dicts into a custom version of extras to avoid triggering SQLAlchemy queries
        group.custom_extras = extras_by_group.get(gid, {})

        # Add subtree dataset counts to groups
        group.subtree_dataset_count = dataset_counts.get(gid, 0)

    groups_by_member = {}
    for m in members:
        groups_by_member.setdefault(m.table_id, []).append(m.group_id)

    parent_child_id_map = {pid: groups_by_member.get(pid, []) for pid in parent_ids}

    def group_descendants(rid):
        group_child_ids = (cid for cid in parent_child_id_map.get(rid, []) if cid in groups_by_id)
        group_children = sorted((groups_by_id[cid] for cid in group_child_ids), key=lambda ch: ch.title)
        for child in group_children:
            if not child:
                continue

            yield (child.id, child.name, child.title, rid, child.subtree_dataset_count, child.custom_extras)
            for descendant in group_descendants(child.id):
                yield descendant

    if not force_root_ids:
        roots = [g for g in groups if g.id not in child_ids]
    else:
        roots = [g for g in groups if g.id in force_root_ids]

    children = {r.id: [c for c in group_descendants(r.id)] for r in roots}

    return roots, children


@logic.side_effect_free
@p.toolkit.chained_action
def group_tree(original_action, context, data_dict):
    '''Returns the full group tree hierarchy.

    :returns: list of top-level GroupTreeNodes
    '''
    top_level_groups, children = _fetch_all_organizations(user=context.get('user'),
                                                          only_approved=p.toolkit.asbool(data_dict.get('only_approved',
                                                                                                       False)))
    sorted_top_level_groups = sorted(top_level_groups, key=lambda g: g.name)
    result = [_group_tree_branch(group, children=children.get(group.id, []))
              for group in sorted_top_level_groups]
    return result


@logic.side_effect_free
@p.toolkit.chained_action
def group_tree_section(original_action, context, data_dict):
    '''Returns the section of the group tree hierarchy which includes the given
    group, from the top-level group downwards.
    :param id: the id or name of the group to include in the tree
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

    # Not supported
    # include_parents = context.get('include_parents', True)
    # include_siblings = context.get('include_siblings', True)

    roots = []
    children = {}
    if group.state == u'active':
        # An optimal solution would be a recursive SQL query just for this, but this is fast enough for <10k organizations
        roots, children = _fetch_all_organizations(user=context.get('user'), force_root_ids=[group.id])

    if len(roots) > 0:
        return _group_tree_branch(roots[0], highlight_group_name=group.name, children=children.get(group.id, []))
    else:
        group.subtree_dataset_count = 0
        group.custom_extras = {}
        return _group_tree_branch(group)


def _group_tree_branch(root_group, highlight_group_name=None, children=[]):
    '''Returns a branch of the group tree hierarchy, rooted in the given group.

    :param root_group_id: group object at the top of the part of the tree
    :param highlight_group_name: group name that is to be flagged 'highlighted'
    :returns: the top GroupTreeNode of the tree
    '''
    nodes = {}  # group_id: GroupTreeNode()
    root_node = nodes[root_group.id] = GroupTreeNode(
        {'id': root_group.id,
         'name': root_group.name,
         'title': root_group.title,
         'dataset_count': root_group.subtree_dataset_count})

    root_node.update(root_group.custom_extras)
    if root_group.name == highlight_group_name:
        nodes[root_group.id].highlight()
        highlight_group_name = None

    for group_id, group_name, group_title, parent_id, dataset_count, extras in children:
        node = GroupTreeNode({'id': group_id,
                              'name': group_name,
                              'title': group_title,
                              'dataset_count': dataset_count})
        if extras:
            node.update(extras)

        nodes[parent_id].add_child_node(node)

        if highlight_group_name and group_name == highlight_group_name:
            node.highlight()

        nodes[group_id] = node

    return root_node
