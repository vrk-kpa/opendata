from collections import namedtuple
from ckan import model
from ckan.model import Package, Session, Resource, PackageExtra, ResourceGroup
from ckan.lib.dictization.model_dictize import resource_dictize
from sqlalchemy import or_, and_

def five_stars():
    """
    Return a list of dicts: 1 for each dataset that has an 'openness_score' extra 
    
    Each dict is of the form:
        {'name': <Dataset Name>, 'title': <Dataset Title>, 'openness_score': <Score>} 
    """
    query = Session.query(
        Package.name,
        Package.title,
        PackageExtra.key, 
        PackageExtra.value, 
    ).join(PackageExtra
    ).filter(
        PackageExtra.key=='openness_score',
    ).distinct(
    ).order_by(Package.title)

    results = []
    for row in query:
        results.append({
            'name': row[0],
            'title': row[1],
            'openness_score': row[3],
        })
    return results

def broken_resource_links_by_dataset():
    """
    Return a list of named tuples, one for each dataset that contains
    broken resource links (defined as resources with an openness score of 0).

    The named tuple is of the form:
        (name (str), title (str), resources (list of dicts))
    """
    query = Session.query(
        Package.name,
        Package.title,
        Resource
    ).join(PackageExtra
    ).join(ResourceGroup
    ).join(Resource
    ).filter(PackageExtra.key == 'openness_score'
    ).filter(
        or_(
            Resource.extras.like('%"openness_score": 0%'),
            Resource.extras.like('%"openness_score": "0"%')
        )
    ).distinct()

    context = {'model': model, 'session': model.Session}
    results = {}
    for name, title, resource in query:
        resource = resource_dictize(resource, context)
        if name in results:
            results[name].resources.append(resource)
        else:
            PackageTuple = namedtuple('PackageTuple', ['name', 'title', 'resources'])
            results[name] = PackageTuple(
                name, title or name, [resource]
            )
    return results.values()

def broken_resource_links_by_dataset_for_organisation(organisation_id):
    result = _get_broken_resource_links(organisation_id)
    return dict(
        id = result.keys()[0][1],
        title = result.keys()[0][0],
        packages = result.values()[0],
    )

def organisations_with_broken_resource_links_by_name():
    result = _get_broken_resource_links().keys()
    result.sort()
    return result

def organisations_with_broken_resource_links():
    return _get_broken_resource_links()
    

def _get_broken_resource_links(organisation_id=None):
    organisations_by_id = _collapse(
        Session.query(
            Package.title,
            PackageExtra.value, 
            Package.name,
            Resource,
        )
        .join(PackageExtra)
        .join(ResourceGroup)
        .join(Resource)
        .filter(Resource.extras.like('%"openness_score": 0%'))
        .filter(
            or_(
                Resource.extras.like('%"openness_score": 0%'),
                Resource.extras.like('%"openness_score": "0"%')
            )
        )
        .filter(
            or_(
                and_(PackageExtra.key=='published_by', PackageExtra.value.like('%%[%s]'%(organisation_id is None and '%' or organisation_id))),
                and_(PackageExtra.key=='published_via', PackageExtra.value.like('%%[%s]'%(organisation_id is None and '%' or organisation_id))),
            )
        )
        .distinct(), 
        [
            _extract_publisher,
            _extract_package,
        ]
    )
    return organisations_by_id 

def _collapser(data, key_func=None):
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

def _collapse(query, fn):
    first = _collapser(query.all(), fn[0])
    result = {}
    for k, v in first.items():
        result[k] = _collapser(v, fn[1])
    return result

def _extract_publisher(row):
    publisher = row[1]
    parts = publisher.split('[')
    try:
        pub_parts = (parts[0].strip(), parts[1][:-1])
    except:
        raise Exception('Could not get the ID from %r' % publisher)
    else:
        return [pub_parts] + [row[0]] + list(row[2:])

def _extract_package(row):
    return [(row[0], row[1])] + list(row[2:])
