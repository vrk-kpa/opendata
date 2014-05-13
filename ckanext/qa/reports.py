from collections import Counter
import copy

import ckan.model as model
import ckan.plugins as p
from ckan.lib.helpers import json, OrderedDict
from ckan.lib.search.query import PackageSearchQuery
from ckanext.dgu.lib.publisher import go_down_tree
from ckan.lib.base import abort

import logging

log = logging.getLogger(__name__)


def openness_report(organization, include_sub_organizations=False):
    if organization is None:
        return openness_index(include_sub_organizations=include_sub_organizations)
    else:
        return openness_for_organization(organization=organization, include_sub_organizations=include_sub_organizations)


def openness_index(include_sub_organizations=False):
    '''Returns the counts of 5 stars of openness for all organizations.'''

    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    total_score_counts = Counter()
    counts = {}
    # Get all the scores and build up the results by org
    for org in model.Session.query(model.Group)\
                          .filter(model.Group.type == 'organization')\
                          .filter(model.Group.state == 'active').all():
        scores = []
        for pkg in org.packages():
            try:
                qa = p.toolkit.get_action('qa_package_openness_show')(context, {'id': pkg.id})
            except p.toolkit.ObjectNotFound:
                log.warning('No QA info for package %s', pkg.name)
                return
            scores.append(qa['openness_score'])
        score_counts = Counter(scores)
        total_score_counts += score_counts
        counts[org.name] = {
            'organization_title': org.title,
            'score_counts': score_counts,
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
                counts_with_sub_orgs[org_name]['score_counts'] += \
                        counts[sub_org_name]['score_counts']
        results = counts_with_sub_orgs
    else:
        results = counts

    data = []
    for org_name, org_counts in sorted(results.iteritems(), key=lambda r: r[0]):
        total_stars = sum([k*v for k, v in org_counts['score_counts'].items() if k])
        num_pkgs_scored = sum([v for k, v in org_counts['score_counts'].items()
                              if k is not None])
        average_stars = round(float(total_stars) / num_pkgs_scored, 1) \
                        if num_pkgs_scored else 0.0
        row = OrderedDict((
            ('organization_title', results[org_name]['organization_title']),
            ('organization_name', org_name),
            ('total_stars', total_stars),
            ('average_stars', average_stars),
            ))
        row.update(org_counts['score_counts'])
        data.append(row)

    # Get total number of packages & resources
    num_packages = model.Session.query(model.Package)\
                        .filter_by(state='active')\
                        .count()
    return {'data': data,
            'total_score_counts': total_score_counts,
            'num_packages_scored': sum(total_score_counts.values()),
            'num_packages': num_packages,
            }

def openness_for_organization(organization=None, include_sub_organizations=False):
    org = model.Group.get(organization)

    if not include_sub_organizations:
        orgs = [org]
    else:
        orgs = org.get_children_group_hierarchy(type='organization')

    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    score_counts = Counter()
    rows = []
    for org in orgs:
        for pkg in org.packages():
            try:
                qa = p.toolkit.get_action('qa_package_openness_show')(context, {'id': pkg.id})
            except p.toolkit.ObjectNotFound:
                log.warning('No QA info for package %s', pkg.name)
                return
            rows.append(OrderedDict((
                ('dataset_name', pkg.name),
                ('dataset_title', pkg.title),
                ('organization_name', org.name),
                ('organization_title', org.title),
                ('openness_score', qa['openness_score']),
                ('openness_score_reason', qa['openness_score_reason']),
                )))
            score_counts[qa['openness_score']] += 1

    total_stars = sum([k*v for k, v in score_counts.items() if k])
    average_stars = round(float(total_stars) /
                          sum([v for k, v in score_counts.items()
                              if k is not None]), 1)

    # Get total number of packages & resources
    num_packages = model.Session.query(model.Package)\
                        .filter_by(owner_org=org.id)\
                        .filter_by(state='active')\
                        .count()
    return {'data': rows,
            'score_counts': score_counts,
            'total_stars': total_stars,
            'average_stars': average_stars,
            'num_packages_scored': len(rows),
            'num_packages': num_packages,
            }


def openness_report_combinations():
    for organization in all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
            yield {'organization': organization,
                   'include_sub_organizations': include_sub_organizations}


openness_report_info = {
    'name': 'openness',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': openness_report_combinations,
    'generate': openness_report,
    'template': 'reports/openness.html',
    }


def all_organizations(include_none):
    if include_none:
        yield None
    organizations = model.Session.query(model.Group).\
        filter(model.Group.type=='organization').\
        filter(model.Group.state=='active').order_by('name')
    for organization in organizations:
        yield organization.name
