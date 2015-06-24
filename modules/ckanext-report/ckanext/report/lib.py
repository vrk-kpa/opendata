'''
These functions are for use by other extensions for their reports.
'''

import ckan.plugins as p


def all_organizations(include_none=False):
    '''Yields all the organization names, and also None if requested. Useful
    when assembling option_combinations'''
    from ckan import model
    if include_none:
        yield None
    organizations = model.Session.query(model.Group).\
        filter(model.Group.type=='organization').\
        filter(model.Group.state=='active').order_by('name')
    for organization in organizations:
        yield organization.name


def go_down_tree(organization):
    '''Provided with an organization object, it walks down the hierarchy and yields
    each organization, including the one you supply.

    Essentially this is a slower version of Group.get_children_group_hierarchy
    because it returns Group objects, rather than dicts.
    '''
    yield organization
    for child in organization.get_children_groups(type='organization'):
        for grandchild in go_down_tree(child):
            yield grandchild


def filter_by_organizations(query, organization, include_sub_organizations):
    '''Given an SQLAlchemy ORM query object, it returns it filtered by the
    given organization and optionally its sub organizations too.
    '''
    from ckan import model
    if not organization:
        return query
    if isinstance(organization, basestring):
        organization = model.Group.get(organization)
        assert organization
    if include_sub_organizations:
        orgs = sorted([x for x in go_down_tree(organization)], key=lambda x: x.name)
        org_ids = [org.id for org in orgs]
        return query.filter(model.Package.owner_org.in_(org_ids))
    else:
        return query.filter(model.Package.owner_org == organization.id)


def dataset_notes(pkg):
    '''Returns a string with notes about the given package. It is
    configurable.'''
    from pylons import config
    expression = config.get('ckanext-report.notes.dataset')
    if not expression:
        return ''
    return eval(expression, None, {'pkg': pkg, 'asbool': p.toolkit.asbool})


def percent(numerator, denominator):
    if denominator == 0:
        return 100 if numerator else 0
    return int((numerator * 100.0) / denominator)
