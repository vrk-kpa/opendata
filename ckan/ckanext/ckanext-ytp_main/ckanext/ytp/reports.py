from ckan.plugins.toolkit import get_action
from ckanext.matomo.model import PackageStats
from .cli import package_generator
from datetime import timedelta, datetime
import iso8601
import logging
from functools import reduce

log = logging.getLogger(__name__)


def administrative_branch_summary_report():
    org_names = [
        'ulkoministerio',
        'sisaministerio',
        'liikenne-ja-viestintaministerio',
        'maa-ja-metsatalousministerio',
        'oikeusministerio',
        'opetus-ja-kulttuuriministerio',
        'puolustusministerio',
        'sosiaali-ja-terveysministerio',
        'tyo-ja-elinkeinoministerio',
        'valtioneuvoston-kanslia',
        'valtiovarainministerio',
        'ymparistoministerio',
    ]

    context = {}

    # Optimization opportunity: Could fetch all orgs here and manually create the hierarchy
    orgs = get_action('organization_list')(context, {'organizations': org_names, 'all_fields': True})

    org_trees = [get_action('group_tree_section')(context, {'id': org['id'], 'type': 'organization'})
                 for org in orgs]

    def children(dataset):
        return dataset['children']

    org_levels = {
        org['name']: level
        for t in org_trees
        for org, level in hierarchy_levels(t, children)}

    flat_orgs = (org for t in org_trees for org in flatten(t, children))

    def with_totals(orgs):
        for org in orgs:
            if org_levels[org['name']] == 0:
                total_org = org.copy()
                total_org['total_org'] = True
                yield total_org
            org['total_org'] = False
            yield org

    root_tree_ids_pairs = (
        (r, [x['id'] for x in (flatten(r, children) if r['total_org'] else [r])])
        for r in with_totals(flat_orgs))

    # Optimization opportunity: Prefetch datasets for all related orgs in one go
    root_datasets_pairs = (
        (k, list(package_generator('owner_org:(%s)' % ' OR '.join(v), 1000, context)))
        for k, v in root_tree_ids_pairs)

    try:
        get_action('qa_package_openness_show')
        qa_enabled = True
    except Exception:
        qa_enabled = False

    return {
        'now': datetime.today().strftime('%d.%m.%Y'),
        'yrs_ago_1': (datetime.today() - timedelta(1 * 365)).strftime('%d.%m.%Y'),
        'yrs_ago_2': (datetime.today() - timedelta(2 * 365)).strftime('%d.%m.%Y'),
        'yrs_ago_3': (datetime.today() - timedelta(3 * 365)).strftime('%d.%m.%Y'),
        'qa_enabled': qa_enabled,
        'table': [{
            'organization': org['title'] if not org['total_org'] else org['title'] + "'s administrative branch",
            'level': org_levels[org['name']],
            'total': org['total_org'],
            'dataset_count': len(datasets),
            'dataset_count_1yr': glen(d for d in datasets if age(d) >= timedelta(1 * 365)),
            'dataset_count_2yr': glen(d for d in datasets if age(d) >= timedelta(2 * 365)),
            'dataset_count_3yr': glen(d for d in datasets if age(d) >= timedelta(3 * 365)),
            'new_datasets_month': glen(d for d in datasets if age(d) <= timedelta(30)),
            'new_datasets_6_months': glen(d for d in datasets if age(d) <= timedelta(6 * 30)),
            'resource_formats': resource_formats(datasets),
            'openness_score_avg': openness_score_avg(context, datasets) if qa_enabled else None
        }
            for org, datasets in root_datasets_pairs
        ]
    }


administrative_branch_summary_report_info = {
    'name': 'administrative-branch-summary-report',
    'title': 'Administrative Branch Summary',
    'description': 'Dataset statistics by administrative branch summary',
    'option_defaults': None,
    'option_combinations': None,
    'generate': administrative_branch_summary_report,
    'template': 'report/administrative_branch_summary_report.html',
}


def deprecated_datasets_report():
    # Get packages that are deprecated
    all_deprecated = package_generator('deprecated:true AND private:false', 10, {})

    # Function to loop packages through
    # Get package visit and download data
    # Resolve package structure to match table structure
    def handle_package(pkg):
        resolved_dict = {
            'title': pkg["title"],
            'id': pkg["id"],
            'maintainer_name': pkg["maintainer"],
            "maintainer_email": pkg["maintainer_email"],
            'metadata_created': pkg["metadata_created"],
            'valid_till': pkg["valid_till"],
        }

        if pkg.get('organization'):
            resolved_dict['organization_title'] = pkg["organization"].get("title")
            resolved_dict['organization_homepage'] = pkg["organization"].get("homepage", None)
            resolved_dict['organization_id'] = pkg["organization"].get("id")

        # FIXME: Against CKAN best practices to access model directly, should be done through actions
        # https://docs.ckan.org/en/ckan-2.7.0/contributing/architecture.html#always-go-through-the-action-functions
        package_stats = PackageStats.get_total_visits(limit=1, package_id=pkg['id'])
        if package_stats:
            resolved_dict['visits'] = package_stats[0].get("visits", 0)
            resolved_dict['downloads'] = package_stats[0].get("downloads", 0)
        else:
            resolved_dict['visits'] = 0
            resolved_dict['downloads'] = 0

        return resolved_dict

    # Loop through all packages and run them through resolver
    map_iterator = list(map(handle_package, all_deprecated))
    packages = list(map_iterator)

    # Filter package output to table:
    # - all deprecated datasets for csv export
    # - limit dataset amount in table (sort by deprecation date, newest deprecation first)
    return {
        'table': packages,
        'top': sorted(packages, key=lambda k: k['valid_till'], reverse=True)[:20]
    }


deprecated_datasets_report_info = {
    'name': 'deprecated-datasets-report',
    'title': 'Deprecated datasets',
    'description': 'Datasets that have deprecated',
    'option_defaults': None,
    'option_combinations': None,
    'generate': deprecated_datasets_report,
    'template': 'report/deprecated_dataset_report.html'
}


def age(dataset):
    return datetime.now() - iso8601.parse_date(dataset['metadata_created'], default_timezone=None)


def glen(generator):
    '''
    Returns the number of items in a generator without interemediate lists
    '''
    return sum(1 for x in generator)


def flatten(x, children):
    '''
    Flatten a hierarchy into an element iterator
    '''
    yield x
    for child in children(x):
        for cx in flatten(child, children):
            yield cx


def hierarchy_levels(x, children, level=0):
    '''
    Provide hierarchy levels for nodes in a hierarchy
    '''
    yield(x, level)
    for child in children(x):
        for cx, cl in hierarchy_levels(child, children, level + 1):
            yield (cx, cl)


def resource_formats(datasets):
    return ', '.join({r['format'] for d in datasets for r in d['resources'] if r['format']})


def openness_score_avg(context, datasets):
    openness_score = get_action('qa_package_openness_show')
    scores = (openness_score(context, {"id": d['id']}) for d in datasets)
    total, count = reduce(tuple_sum, (
        (s['openness_score'], 1)
        for s in scores
        if s.get('openness_score') is not None),
        (0, 0))
    return total / count if count > 0 else None


def tuple_sum(*xs):
    return tuple(sum(x) for x in zip(*xs))
