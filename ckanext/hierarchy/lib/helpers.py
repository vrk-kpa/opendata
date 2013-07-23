from bisect import bisect_right

from ckan import model

# TODO: Add logic layer access for this

class GroupTreeNode(object):
    def __init__(self, group):
        self.group = group
        self.children = []
        # self.children_titles has a 1:1 relationship with values in
        # self.children, and is used to help keep them sorted by title
        self.children_titles = [] 

    def add_child_node(self, child_node):
        '''Adds the child GroupTreeNode to this node, keeping the children
        in alphabetical order by title.
        '''
        title = child_node.group.title
        insert_index = bisect_right(self.children_titles, title)
        self.children.insert(insert_index, child_node)
        self.children_titles.insert(insert_index, title)

def group_tree(type='group'):
    '''Returns the full group tree hierarchy.

    :returns: list of top-level GroupTreeNodes
    '''
    return [group_tree_branch(group, type=type) \
            for group in model.Group.get_top_level_groups(type=type)]

def group_tree_branch(root_group, type='group'):
    '''Returns a branch of the group tree hierarchy, rooted in the given group.

    :param root_group: group at the top of the part of the tree
    :returns: top GroupTreeNode of the tree
    '''
    nodes = {} # group_id: GroupTreeNode()
    root_node = nodes[root_group.id] = GroupTreeNode(root_group)
    for group, parent_id in root_group.get_children_group_hierarchy(type=type):
        nodes[group.id] = GroupTreeNode(group)
        nodes[parent_id].add_child_node(nodes[group.id])
    return root_node

