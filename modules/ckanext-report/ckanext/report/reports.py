'''
Working examples - simple tag report.
'''

from ckan import model
from ckan.lib.helpers import OrderedDict
from ckanext.report import lib


def tagless_report(organization, include_sub_organizations=False):
    '''
    Produces a report on packages without tags.
    Returns something like this:
        {
         'table': [
            {'name': 'river-levels', 'title': 'River levels', 'notes': 'Harvested', 'user': 'bob', 'created': '2008-06-13T10:24:59.435631'},
            {'name': 'co2-monthly', 'title' 'CO2 monthly', 'notes': '', 'user': 'bob', 'created': '2009-12-14T08:42:45.473827'},
            ],
         'num_packages': 56,
         'packages_without_tags_percent': 4,
         'average_tags_per_package': 3.5,
        }
    '''
    # Find the packages without tags
    q = model.Session.query(model.Package) \
             .outerjoin(model.PackageTag) \
             .filter(model.PackageTag.id == None)
    if organization:
        q = lib.filter_by_organizations(q, organization,
                                        include_sub_organizations)
    tagless_pkgs = [OrderedDict((
            ('name', pkg.name),
            ('title', pkg.title),
            ('notes', lib.dataset_notes(pkg)),
            ('user', pkg.creator_user_id),
            ('created', pkg.metadata_created.isoformat()),
            )) for pkg in q.slice(0, 100)]  # First 100 only for this demo

    # Average number of tags per package
    q = model.Session.query(model.Package)
    q = lib.filter_by_organizations(q, organization, include_sub_organizations)
    num_packages = q.count()
    q = q.join(model.PackageTag)
    num_taggings = q.count()
    if num_packages:
        average_tags_per_package = round(float(num_taggings) / num_packages, 1)
    else:
        average_tags_per_package = None
    packages_without_tags_percent = lib.percent(len(tagless_pkgs), num_packages)

    return {
        'table': tagless_pkgs,
        'num_packages': num_packages,
        'packages_without_tags_percent': packages_without_tags_percent,
        'average_tags_per_package': average_tags_per_package,
        }

def tagless_report_option_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
            yield {'organization': organization,
                   'include_sub_organizations': include_sub_organizations}

tagless_report_info = {
    'name': 'tagless-datasets',
    'description': 'Datasets which have no tags.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': tagless_report_option_combinations,
    'generate': tagless_report,
    'template': 'report/tagless-datasets.html',
    }
