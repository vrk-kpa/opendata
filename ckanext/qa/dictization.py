import re

from ckan.model import Package, Session

__all__ = ['package_openness_score',
           'packages_with_minimum_one_broken_resource']

def package_openness_score(package_id=None):
    openness_scores = []
    packages = Session.query(Package)
    if package_id:
        packages = packages.filter_by(id=package_id)
    for package in packages:
        openness_scores.append(dict(
            package_id=package.id,
            name=package.name,
            openness_score=package.extras.get('openness_score'),
            openness_score_last_checked=package.extras.get('openness_score_last_checked'),
        ))
    return openness_scores

def packages_with_minimum_one_broken_resource(organization_id=None, organization_name=None):
    broken_packages = []
    packages = Session.query(Package)
    for package in packages:
                    
        if package.extras.get('openness_score') == 0.0:
            
            organization_extras = dict()
            exp = re.compile('\s*(.*?)\s*\[(\d+)\]')
            org_tag = package.extras.get('published_by', package.extras.get('published_via', None))
            match = re.match(exp, org_tag)
            if match:
                groups = match.groups()
                organization_extras = dict(
                    organization_name = groups[0],
                    organization_id = groups[1],
                    published_via = max(package.extras.get('published_via'), False),
                    published_by = max(package.extras.get('published_by'), False),
                )

            if organization_id:
                if not organization_extras.get('organization_id', None) == organization_id:
                    continue

            package_data = dict(
                package_id=package.id,
                name=package.name,
                openness_score=package.extras.get('openness_score'),
                openness_score_last_checked=package.extras.get('openness_score_last_checked'),
                resources=[dict(
                    openness_score=resource.extras.get('openness_score'),
                    openness_score_reason=resource.extras.get('openness_score_reason'),
                    is_bad_link=not bool(resource.extras.get('openness_score')),
                    description=resource.description,
                    url=resource.url,
                    format=resource.format,
                ) for resource in package.resources]
            )
            package_data.update(organization_extras)
            broken_packages.append(package_data)
            
    return broken_packages