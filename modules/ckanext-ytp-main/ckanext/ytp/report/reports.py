from ckan.common import OrderedDict
from ckan.logic import get_action, NotFound, NotAuthorized
import itertools
from datetime import timedelta, datetime

def test_report():
    return {
        'table' : [
            {str(d): (n*8 + d)**2 for d in range(8)}
            for n in range(8)
            ]
    }

test_report_info = {
    'name': 'test-report',
    'title': 'Test Report',
    'description': 'Most Testy Reportie',
    'option_defaults': None,
    'option_combinations': None,
    'generate': test_report,
    'template': 'report/test_report.html',
}

def administrative_branch_summary_report():
    org_names = [
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
    orgs = get_action('organization_list')(context, {'organizations': org_names, 'all_fields': True})
    orgs_by_name = {org['name']: org for org in orgs}

    org_trees = [get_action('group_tree_section')(context, {'id': org['id'], 'type': 'organization'})
                 for org in orgs]
    org_ids_by_tree = {r['name']: [x['id'] for x in flatten(r, lambda x: x['children'])]
        for r in org_trees}
    datasets_by_tree = {k: list(package_generator('owner_org:(%s)' % ' OR '.join(v), 1000, context))
            for k, v in org_ids_by_tree.iteritems()}
    return {
        'table' : [{
            'organization': orgs_by_name[org_name],
            'dataset_count': len(datasets),
            'new_datasets_month': glen(d for d in datasets if age(d) <= timedelta(30)),
            'new_datasets_year': glen(d for d in datasets if age(d) <= timedelta(365)),
            'resource_formats': resource_formats(datasets)
            }
            for org_name, datasets in datasets_by_tree.iteritems()
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

def package_generator(query, page_size, context):
    package_search = get_action('package_search')

    for index in itertools.count(start=0, step=page_size):
        data_dict = {'include_private': True, 'rows': page_size, 'q': query, 'start': index}
        packages = package_search(context, data_dict).get('results', [])
        for package in packages:
            yield package
        else:
            return

def age(dataset):
    return datetime.now() - datetime.strptime(dataset['metadata_created'], '%Y-%m-%dT%H:%M:%S.%f')


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

def resource_formats(datasets):
    return ', '.join(r['format'] for d in datasets for r in d['resources'] if r['format'])
