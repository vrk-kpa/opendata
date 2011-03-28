import re

from ckan.model import Package, Session, Resource, PackageExtra, ResourceGroup
from sqlalchemy import or_, and_



def package_openness_score(package_id=None):
    openness_scores = []
    packages = Session.query(Package)
    if package_id:
        packages = packages.filter_by(id=package_id)
    for package in packages:
        openness_scores.append(
            dict(
                package_id=package.id,
                name=package.name,
                openness_score=package.extras.get('openness_score'),
                openness_score_last_checked=package.extras.get('openness_score_last_checked'),
            )
        )
    return openness_scores

def collapser(data, key_func=None):
    result = {}
    for row in data:
        if key_func:
            row = key_func(row)
        key = row[0]
        if len(row) == 2:
            row = row[1]
        else:
            row = row[1:]
        if key in result:
            result[key].append(row)
        else:
            result[key] = [row]
    return result

def collapse(query, fn):
    first = collapser(query.all(), fn[0])
    result = {}
    for k, v in first.items():
        result[k] = collapser(v, fn[1])
    return result

def extract_publisher(row):
    publisher = row[1]
    parts = publisher.split('[')
    try:
        pub_parts = (parts[1][:-1], parts[0].strip())
    except:
        raise Exception('Could not get the ID from %r'%publisher)
    else:
        return [pub_parts] + [row[0]] + list(row[2:])

def extract_package(row):
    return [(row[0], row[1])] + list(row[2:])

def packages_by_organisation_with_minimum_one_broken_resource():
    organisations_by_id = collapse(
        Session.query(
            Package.title,
            PackageExtra.value, 
            Package.name,
            Resource,
        ).join(PackageExtra
        ).join(ResourceGroup
        ).join(Resource
        ).filter(
            Resource.extras.like('%"openness_score": 0%'),
        ).filter(
            or_(
                and_(PackageExtra.key=='published_by', PackageExtra.value.like('%[%]')),
                and_(PackageExtra.key=='published_via', PackageExtra.value.like('%[%]')),
            )
        ).distinct(), 
        [
             extract_publisher,
             extract_package,
        ]
    )
    return organisations_by_id 














    #for package in packages:
    #    organisations = {}
    #    for name in ['published_by', 'published_via']:
    #        publisher = package.extras.get(name, '').split('[')
    #        if publisher:
    #            id = publisher[1][:-1]
    #            organisations[name] = id
    #            if not organisations_by_id.has_key(id):
    #                name = publisher[0].strip()
    #                organisations_by_id[id] = name
    #    package_data = dict(
    #        package_id=package.id,
    #        name=package.name,
    #        openness_score='-',#package.extras.get('openness_score'),
    #        openness_score_last_checked=package.extras.get('openness_score_last_checked'),
    #        resources=[dict(
    #            openness_score=resource.extras.get('openness_score'),
    #            openness_score_reason=resource.extras.get('openness_score_reason'),
    #            is_bad_link=not bool(resource.extras.get('openness_score')),
    #            description=resource.description,
    #            url=resource.url,
    #            format=resource.format,
    #        ) for resource in packages[package]]#.resources]
    #    )
    #    #package_data.update(organisation_extras)
    #    broken_packages.append(package_data)
    #return broken_packages

def packages_with_minimum_one_broken_resource(organisation_id=None, organisation_name=None):
    broken_packages = []
    packages = {}
    for resource in Session.query(Resource).filter(Resource.extras.like('%"openness_score": 0%')):
        if resource.resource_group.package in packages:
            packages[resource.resource_group.package].append(resource)
        else:
            packages[resource.resource_group.package] = [resource]
    for package in packages:
        package_data = dict(
            package_id=package.id,
            name=package.name,
            openness_score='-',#package.extras.get('openness_score'),
            openness_score_last_checked=package.extras.get('openness_score_last_checked'),
            resources=[dict(
                openness_score=resource.extras.get('openness_score'),
                openness_score_reason=resource.extras.get('openness_score_reason'),
                is_bad_link=not bool(resource.extras.get('openness_score')),
                description=resource.description,
                url=resource.url,
                format=resource.format,
            ) for resource in packages[package]]
        )
        broken_packages.append(package_data)
    return broken_packages
