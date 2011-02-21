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

def packages_with_minimum_one_broken_resource():
    broken_packages = []
    packages = Session.query(Package)
    for package in packages:
        if package.extras.get('openness_score') == 0.0:
            broken_packages.append(dict(
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
            ))
    return broken_packages