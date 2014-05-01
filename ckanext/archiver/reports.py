import copy

import ckan.model as model
from ckan.lib.helpers import OrderedDict

def broken_links(organization, include_sub_organizations=False):
    if organization == None:
        return broken_links_by_organization(include_sub_organizations=include_sub_organizations)
    else:
        return broken_links_for_organization(organization=organization, include_sub_organizations=include_sub_organizations)


# WAS organisations_with_broken_resource_links
def broken_links_by_organization(include_sub_organizations=False):
    '''Returns the count of broken links for all organizations.'''

    from ckanext.archiver.model import Archival

    counts = {}
    # Get all the broken datasets and build up the results by org
    for org in model.Session.query(model.Group)\
                          .filter(model.Group.type == 'organization')\
                          .filter(model.Group.state == 'active').all():
        archivals = model.Session.query(Archival)\
                         .filter(Archival.is_broken == True)\
                         .join(model.Package, Archival.package_id == model.Package.id)\
                         .filter(model.Package.owner_org == org.id)\
                         .filter(model.Package.state == 'active')\
                         .join(model.Resource, Archival.resource_id == model.Resource.id)\
                         .filter(model.Resource.state == 'active')
        broken_resources = archivals.count()
        broken_datasets = archivals.distinct(model.Package.id).count()
        counts[org.name] = {
            'organization_title': org.title,
            'packages': broken_datasets,
            'resources': broken_resources
        }

    counts_with_sub_orgs = copy.deepcopy(counts)  # new dict
    if include_sub_organizations:
        for org_name in counts_with_sub_orgs:
            org = model.Group.by_name(org_name)

            for sub_org_id, sub_org_name, sub_org_title, sub_org_parent_id \
                    in org.get_children_group_hierarchy(type='organization'):
                if sub_org_name not in counts:
                    # occurs only if there is an organization created since the last loop?
                    continue
                counts_with_sub_orgs[org_name]['packages'] += \
                        counts[sub_org_name]['packages']
                counts_with_sub_orgs[org_name]['resources'] += \
                        counts[sub_org_name]['resources']
        results = counts_with_sub_orgs
    else:
        results = counts

    data = []
    for org_name, org_counts in sorted(results.iteritems(), key=lambda r: r[0]):
        #if results[org_counts]['resources'] == 0:
        #    continue

        data.append(OrderedDict((
            ('organization_title', results[org_name]['organization_title']),
            ('organization_name', org_name),
            ('broken_package_count', org_counts['packages']),
            ('broken_resource_count', org_counts['resources']),
            )))

    return {'data': data}


def broken_links_for_organization(organization, include_sub_organizations=False):
    '''
    Returns a dictionary detailing broken resource links for the organization
    or if organization it returns the index page for all organizations.

    params:
      organization - name of an organization

    Returns:
    {'organization_name': 'cabinet-office',
     'organization_title:': 'Cabinet Office',
     'data': [
       {'package_name', 'package_title', 'resource_url', 'status', 'reason', 'last_success', 'first_failure', 'failure_count', 'last_updated'}
      ...]

    '''
    from ckanext.archiver.model import Archival

    if organization == None:
        return broken_links_by_organization(include_sub_organizations=include_sub_organizations)

    org = model.Group.get(organization)

    name = org.name
    title = org.title

    archivals = model.Session.query(Archival, model.Package, model.Group).\
        filter(Archival.is_broken == True).\
        join(model.Package, Archival.package_id == model.Package.id).\
        filter(model.Package.state == 'active').\
        join(model.Resource, Archival.resource_id == model.Resource.id).\
        filter(model.Resource.state == 'active')

    if not include_sub_organizations:
        archivals = archivals.filter(model.Package.owner_org == org.id)
    else:
        # We want any organization_id that is part of this organization's tree
        org_ids = ['%s' % organization.id for organization in go_down_tree(org)]
        archivals = archivals.filter(model.Package.owner_org.in_(org_ids))

    archivals = archivals.join(model.Group, model.Package.owner_org == model.Group.id)

    results = []

    for archival, pkg, org in archivals.all():
        pkg = model.Package.get(archival.package_id)
        resource = model.Resource.get(archival.resource_id)

        via = ''
        er = pkg.extras.get('external_reference', '')
        if er == 'ONSHUB':
            via = "Stats Hub"
        elif er.startswith("DATA4NR"):
            via = "Data4nr"

        archived_resource = model.Session.query(model.ResourceRevision)\
                            .filter_by(id=resource.id)\
                            .filter_by(revision_timestamp=archival.resource_timestamp)\
                            .first() or resource
        row_data = OrderedDict((
            ('dataset_title', pkg.title),
            ('dataset_name', pkg.name),
            ('organization_title', org.title),
            ('organization_name', org.name),
            ('resource_position', resource.position),
            ('resource_id', resource.id),
            ('resource_url', archived_resource.url),
            ('url_up_to_date', resource.url == archived_resource.url),
            ('via', via),
            ('first_failure', archival.first_failure),
            ('last_updated', archival.updated),
            ('last_success', archival.last_success),
            ('url_redirected_to', archival.url_redirected_to),
            ('reason', archival.reason),
            ('status', archival.status),
            ('failure_count', archival.failure_count),
            ))

        results.append(row_data)

    num_packages = archivals.distinct(model.Package.name).count()
    num_resources = len(results)

    return {'organization_name': name,
            'organization_title': title,
            'broken_package_count': num_packages,
            'broken_resource_count': num_resources,
            'data': results}


def broken_links_option_combinations():
    for organization in all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
            yield {'organization': organization,
                   'include_sub_organizations': include_sub_organizations}


broken_links_report_info = {
    'name': 'broken-links',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': broken_links_option_combinations,
    'generate': broken_links,
    'template': 'reports/broken_links.html',
    }


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

def all_organizations(include_none):
    if include_none:
        yield None
    organizations = model.Session.query(model.Group).\
        filter(model.Group.type=='organization').\
        filter(model.Group.state=='active').order_by('name')
    for organization in organizations:
        yield organization.name
