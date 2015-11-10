import copy

import ckan.model as model
from ckan.lib.helpers import OrderedDict
import ckan.plugins as p
from ckanext.report import lib

def broken_links(organization, include_sub_organizations=False):
    if organization is None:
        return broken_links_index(include_sub_organizations=include_sub_organizations)
    else:
        return broken_links_for_organization(organization=organization, include_sub_organizations=include_sub_organizations)


def broken_links_index(include_sub_organizations=False):
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
        num_datasets = model.Session.query(model.Package)\
            .filter_by(owner_org=org.id)\
            .filter_by(state='active')\
            .count()
        num_resources = model.Session.query(model.Package)\
            .filter_by(owner_org=org.id)\
            .filter_by(state='active')
        if hasattr(model, 'ResourceGroup'):
            num_resources = num_resources.join(model.ResourceGroup)
        num_resources = num_resources \
            .join(model.Resource)\
            .filter_by(state='active')\
            .count()
        counts[org.name] = {
            'organization_title': org.title,
            'broken_packages': broken_datasets,
            'broken_resources': broken_resources,
            'packages': num_datasets,
            'resources': num_resources
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
                counts_with_sub_orgs[org_name]['broken_packages'] += \
                        counts[sub_org_name]['broken_packages']
                counts_with_sub_orgs[org_name]['broken_resources'] += \
                        counts[sub_org_name]['broken_resources']
                counts_with_sub_orgs[org_name]['packages'] += \
                        counts[sub_org_name]['packages']
                counts_with_sub_orgs[org_name]['resources'] += \
                        counts[sub_org_name]['resources']
        results = counts_with_sub_orgs
    else:
        results = counts

    data = []
    num_broken_packages = 0
    num_broken_resources = 0
    num_packages = 0
    num_resources = 0
    for org_name, org_counts in sorted(results.iteritems(), key=lambda r: r[0]):
        data.append(OrderedDict((
            ('organization_title', results[org_name]['organization_title']),
            ('organization_name', org_name),
            ('package_count', org_counts['packages']),
            ('resource_count', org_counts['resources']),
            ('broken_package_count', org_counts['broken_packages']),
            ('broken_package_percent', lib.percent(org_counts['broken_packages'], org_counts['packages'])),
            ('broken_resource_count', org_counts['broken_resources']),
            ('broken_resource_percent', lib.percent(org_counts['broken_resources'], org_counts['resources'])),
            )))
        # Totals - always use the counts, rather than counts_with_sub_orgs, to
        # avoid counting a package in both its org and parent org
        org_counts_ = counts[org_name]
        num_broken_packages += org_counts_['broken_packages']
        num_broken_resources += org_counts_['broken_resources']
        num_packages += org_counts_['packages']
        num_resources += org_counts_['resources']

    return {'table': data,
            'num_broken_packages': num_broken_packages,
            'num_broken_resources': num_broken_resources,
            'num_packages': num_packages,
            'num_resources': num_resources,
            'broken_package_percent': lib.percent(num_broken_packages, num_packages),
            'broken_resource_percent': lib.percent(num_broken_resources, num_resources),
            }


def broken_links_for_organization(organization, include_sub_organizations=False):
    '''
    Returns a dictionary detailing broken resource links for the organization
    or if organization it returns the index page for all organizations.

    params:
      organization - name of an organization

    Returns:
    {'organization_name': 'cabinet-office',
     'organization_title:': 'Cabinet Office',
     'table': [
       {'package_name', 'package_title', 'resource_url', 'status', 'reason', 'last_success', 'first_failure', 'failure_count', 'last_updated'}
      ...]

    '''
    from ckanext.archiver.model import Archival

    org = model.Group.get(organization)
    if not org:
        raise p.toolkit.ObjectNotFound()

    name = org.name
    title = org.title

    archivals = model.Session.query(Archival, model.Package, model.Group).\
        filter(Archival.is_broken == True).\
        join(model.Package, Archival.package_id == model.Package.id).\
        filter(model.Package.state == 'active').\
        join(model.Resource, Archival.resource_id == model.Resource.id).\
        filter(model.Resource.state == 'active')

    if not include_sub_organizations:
        org_ids = [org.id]
        archivals = archivals.filter(model.Package.owner_org == org.id)
    else:
        # We want any organization_id that is part of this organization's tree
        org_ids = ['%s' % organization.id for organization in lib.go_down_tree(org)]
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
            ('dataset_notes', lib.dataset_notes(pkg)),
            ('organization_title', org.title),
            ('organization_name', org.name),
            ('resource_position', resource.position),
            ('resource_id', resource.id),
            ('resource_url', archived_resource.url),
            ('url_up_to_date', resource.url == archived_resource.url),
            ('via', via),
            ('first_failure', archival.first_failure.isoformat() if archival.first_failure else None),
            ('last_updated', archival.updated.isoformat() if archival.updated else None),
            ('last_success', archival.last_success.isoformat() if archival.last_success else None),
            ('url_redirected_to', archival.url_redirected_to),
            ('reason', archival.reason),
            ('status', archival.status),
            ('failure_count', archival.failure_count),
            ))

        results.append(row_data)

    num_broken_packages = archivals.distinct(model.Package.name).count()
    num_broken_resources = len(results)

    # Get total number of packages & resources
    num_packages = model.Session.query(model.Package)\
                        .filter(model.Package.owner_org.in_(org_ids))\
                        .filter_by(state='active')\
                        .count()
    num_resources = model.Session.query(model.Resource)\
                         .filter_by(state='active')
    if hasattr(model, 'ResourceGroup'):
        num_resources = num_resources.join(model.ResourceGroup)
    num_resources = num_resources \
        .join(model.Package)\
        .filter(model.Package.owner_org.in_(org_ids))\
        .filter_by(state='active').count()

    return {'organization_name': name,
            'organization_title': title,
            'num_broken_packages': num_broken_packages,
            'num_broken_resources': num_broken_resources,
            'num_packages': num_packages,
            'num_resources': num_resources,
            'broken_package_percent': lib.percent(num_broken_packages, num_packages),
            'broken_resource_percent': lib.percent(num_broken_resources, num_resources),
            'table': results}


def broken_links_option_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
            yield {'organization': organization,
                   'include_sub_organizations': include_sub_organizations}


broken_links_report_info = {
    'name': 'broken-links',
    'description': 'Dataset resource URLs that are found to result in errors when resolved.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': broken_links_option_combinations,
    'generate': broken_links,
    'template': 'report/broken_links.html',
    }
