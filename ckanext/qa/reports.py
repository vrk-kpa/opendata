from collections import namedtuple
from ckan import model
from ckan.model import Package, Session, Resource, PackageExtra, ResourceGroup, TaskStatus
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.logic import get_action
from sqlalchemy import or_, and_, func

def five_stars():
    """
    Return a list of dicts: 1 for each dataset that has an openness score.
    
    Each dict is of the form:
        {'name': <Dataset Name>, 'title': <Dataset Title>, 'openness_score': <Score>} 
    """
    # take the maximum openness score among dataset resources to be the
    # overall dataset openness core
    query = Session.query(Package.name, Package.title, 
                          func.max(TaskStatus.value).label('value'))\
        .join(ResourceGroup, Package.id==ResourceGroup.package_id)\
        .join(Resource)\
        .join(TaskStatus, TaskStatus.entity_id==Resource.id)\
        .filter(TaskStatus.key==u'openness_score')\
        .group_by(Package.name, Package.title)\
        .distinct()

    results = []
    for row in query:
        results.append({
            'name': row.name,
            'title': row.title,
            'openness_score': row.value
        })

    return results

def broken_resource_links_by_dataset():
    """
    Return a list of named tuples, one for each dataset that contains
    broken resource links (defined as resources with an openness score of 0).

    The named tuple is of the form:
        (name (str), title (str), resources (list of dicts))
    """
    query = Session.query(Package.name, Package.title, Resource)\
        .join(ResourceGroup, Package.id==ResourceGroup.package_id)\
        .join(Resource)\
        .join(TaskStatus, TaskStatus.entity_id==Resource.id)\
        .filter(TaskStatus.key==u'openness_score')\
        .filter(TaskStatus.value==u'0')\
        .distinct()

    context = {'model': model, 'session': model.Session}
    results = {}
    for name, title, resource in query:
        resource = resource_dictize(resource, context)

        data = {'entity_id': resource['id'], 'task_type': 'qa', 'key': 'openness_score_reason'}
        status = get_action('task_status_show')(context, data)
        resource['openness_score_reason'] = status.get('value')

        if name in results:
            results[name].resources.append(resource)
        else:
            DatasetTuple = namedtuple('DatasetTuple', ['name', 'title', 'resources'])
            results[name] = DatasetTuple(name, title or name, [resource])

    return results.values()

def broken_resource_links_by_dataset_for_organisation(organisation_id):
    result = _get_broken_resource_links(organisation_id)
    return {
        'id': result.keys()[0][1],
        'title': result.keys()[0][0],
        'packages': result.values()[0]
    }

def organisations_with_broken_resource_links_by_name():
    result = _get_broken_resource_links().keys()
    result.sort()
    return result

def organisations_with_broken_resource_links():
    return _get_broken_resource_links()
    
def _get_broken_resource_links(organisation_id=None):
    organisation_id = None

    query = Session.query(Package.name, Package.title, PackageExtra.value, Resource)\
            .join(PackageExtra)\
            .join(ResourceGroup, Package.id==ResourceGroup.package_id)\
            .join(Resource)\
            .join(TaskStatus, TaskStatus.entity_id==Resource.id)\
            .filter(TaskStatus.key==u'openness_score')\
            .filter(TaskStatus.value==u'0')\
            .filter(or_(
                and_(PackageExtra.key=='published_by', 
                     PackageExtra.value.like('%%[%s]' % (organisation_id is None and '%' or organisation_id))),
                and_(PackageExtra.key=='published_via', 
                     PackageExtra.value.like('%%[%s]' % (organisation_id is None and '%' or organisation_id))),
                )\
            )\
            .distinct()

    context = {'model': model, 'session': model.Session}
    data = []
    for row in query:
        resource = resource_dictize(row.Resource, context)
        task_data = {'entity_id': resource['id'], 'task_type': 'qa', 'key': 'openness_score_reason'}
        status = get_action('task_status_show')(context, task_data)
        resource['openness_score'] = u'0'
        resource['openness_score_reason'] = status.get('value')

        data.append([row.name, row.title, row.value, resource])

    return _collapse(data, [_extract_publisher, _extract_dataset])

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

def _collapse(data, fn):
    first = _collapser(data, fn[0])
    result = {}
    for k, v in first.items():
        result[k] = _collapser(v, fn[1])
    return result

def _extract_publisher(row):
    """
    Extract publisher info from a query result row.
    Each row should be a list of the form [name, title, value, Resource]

    Returns a list of the form:

        [<publisher tuple>, <other elements in row tuple>]
    """
    publisher = row[2]
    parts = publisher.split('[')
    try:
        pub_parts = (parts[0].strip(), parts[1][:-1])
    except:
        raise Exception('Could not get the ID from %r' % publisher)
    else:
        return [pub_parts] + [row[0], row[1], row[3]]

def _extract_dataset(row):
    """
    Extract dataset info form a query result row.
    Each row should be a list of the form [name, title, Resource]

    Returns a list of the form:

        [(name, title), Resource]
    """
    return [(row[0], row[1]), row[2]]

