from collections import namedtuple
from sqlalchemy.util import OrderedDict
from sqlalchemy import or_, and_, func
import ckan.model as model
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize

import logging

log = logging.getLogger(__name__)

resource_dictize = model_dictize.resource_dictize

class DictObj(dict):
    """\
    Like a normal Python dictionary, but allows keys to be accessed as
    attributes. For example:

    ::

        >>> person = DictObj(firstname='James')
        >>> person.firstname
        'James'
        >>> person['surname'] = 'Jones'
        >>> person.surname
        'Jones'

    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('No such attribute %r'%name)

    def __setattr__(self, name, value):
        raise AttributeError(
            'You cannot set attributes of this DictObject directly'
        )

def five_stars(id=None):
    """
    Return a list of dicts: 1 for each dataset that has an openness score.

    Each dict is of the form:
        {'name': <string>, 'title': <string>, 'openness_score': <int>}
    """
    if id:
        pkg = model.Package.get(id)
        if not pkg:
            return "Not found"

    # take the maximum openness score among dataset resources to be the
    # overall dataset openness core
    query = model.Session.query(model.Package.name, model.Package.title,
                                func.max(model.TaskStatus.value).label('value'))\
        .join(model.ResourceGroup, model.Package.id == model.ResourceGroup.package_id)\
        .join(model.Resource)\
        .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
        .filter(model.TaskStatus.key==u'openness_score')\
        .filter(model.Package.state==u'active')\
        .filter(model.Resource.state==u'active')\
        .filter(model.ResourceGroup.state==u'active')\
        .group_by(model.Package.name, model.Package.title)\
        .order_by(model.Package.title)\
        .distinct()

    if id:
        query = query.filter(model.Package.id == pkg.id)

    results = []
    for row in query:
        results.append({
            'name': row.name,
            'title': row.title,
            'openness_score': row.value
        })
    return results

def resource_five_stars(id):
    """
    Return a dict containing the QA results for a given resource

    Each dict is of the form:
        {'openness_score': <int>, 'openness_score_reason': <string>, 'failure_count': <int>}
    """
    if id:
        r = model.Resource.get(id)
        if not r:
            return {}  # Not found

    context = {'model': model, 'session': model.Session}
    data = {'entity_id': r.id, 'task_type': 'qa'}

    try:
        data['key'] = 'openness_score'
        status = p.toolkit.get_action('task_status_show')(context, data)
        openness_score = int(status.get('value'))
        openness_score_updated = status.get('last_updated')

        data['key'] = 'openness_score_reason'
        status = p.toolkit.get_action('task_status_show')(context, data)
        openness_score_reason = status.get('value')
        openness_score_reason_updated = status.get('last_updated')

        data['key'] = 'openness_score_failure_count'
        status = p.toolkit.get_action('task_status_show')(context, data)
        openness_score_failure_count = int(status.get('value'))
        openness_score_failure_count_updated = status.get('last_updated')

        last_updated = max( 
            openness_score_updated,
            openness_score_reason_updated,
            openness_score_failure_count_updated )

        result = {
            'openness_score': openness_score,
            'openness_score_reason': openness_score_reason,
            'openness_score_failure_count': openness_score_failure_count,
            'openness_score_updated': openness_score_updated,
            'openness_score_reason_updated': openness_score_reason_updated,
            'openness_score_failure_count_updated': openness_score_failure_count_updated,
            'openness_updated': last_updated
        }
    except p.toolkit.DictObjectNotFound:
        result = {}

    return result

def broken_resource_links_by_dataset():
    """
    Return a list of named tuples, one for each dataset that contains
    broken resource links (defined as resources with an openness score of 0).

    The named tuple is of the form:
        (name (str), title (str), resources (list of dicts))
    """
    rows = model.Session.execute(
        """
        select package.id as package_id, task_status.value as reason, resource.url as url, package.title as title, package.name as name
            from task_status 
        left join resource on task_status.entity_id = resource.id
        left join resource_group on resource.resource_group_id = resource_group.id
        left join package on resource_group.package_id = package.id
        where 
            entity_id in (select entity_id from task_status where key='openness_score' and value='0')
        and key='openness_score_reason' 
        and package.state = 'active' 
        and resource.state='active'
        and resource_group.state='active'
        and task_status.value!='License not open'
        order by package.title
        """
    )
    results = OrderedDict()
    for row in rows:
        if results.has_key(row.package_id):
            results[row.package_id]['resources'].append(DictObj(url=row.url, openness_score_reason=row.reason))
        else:
            results[row.package_id] = DictObj(name=row.name, title=row.title, resources=[DictObj(url=row.url, openness_score_reason=row.reason)])
    return results.values()

def broken_resource_links_by_dataset_for_organisation(organisation_id):
    results = _get_broken_resource_links(organisation_id)
    if not results:
        id_ = title = ''
        packages = {}
    else:
        organisation_tuple, package_resource_dict = results.items()[0]
        title, id_ = organisation_tuple
        packages = package_resource_dict
    return {
            'id': id_,
            'title': title,
            'packages': packages,
        }

def organisations_with_broken_resource_links_by_name():
    result = _get_broken_resource_links().keys()
    result.sort()
    return result

def organisations_with_broken_resource_links(include_resources=False):
    return _get_broken_resource_links(include_resources=include_resources)

def _get_broken_resource_links(organisation_name=None, include_resources=False):
    '''
    Returns a dictionary detailing broken resource links, categorised
    by package and organisation (group).

    i.e.:
        {(organisation_title, organisation_name):
         {(package_name, package_title): list_of_broken_resource_dicts}

    Returns all organisations unless you supply a particular organisation_name
    '''
    values = {}
    main_sql =    """
        from task_status 
           left join resource on task_status.entity_id = resource.id
           left join resource_group on resource.resource_group_id = resource_group.id
           left join package on resource_group.package_id = package.id
           left join member on member.table_id = package.id
           left join "group" on member.group_id = "group".id
        where 
           task_status.task_type='archiver'
           and task_status.key='status'
           and task_status.value!='Archived successfully'
           and package.state = 'active'
           and resource.state='active'
           and resource_group.state='active'
           and "group".state='active'
        """
    for reason in not_broken_but_0_stars:
        main_sql += """
        and task_status.value!='%s'
        """ % reason
    if organisation_name:
        values['org_name'] = organisation_name
        sql = """
        select package.id as package_id, task_status.value as reason, task_status.error as error_json, resource.url as url, package.title as title, package.name as name, "group".id as publisher_id, "group".name as publisher_name, "group".title as publisher_title
        """
        sql += main_sql + ' and "group".name = :org_name'
        sql += ' order by package.title'
    elif include_resources:
        sql = """
        select package.id as package_id, task_status.value as reason, task_status.error as error_json, resource.url as url, package.title as title, package.name as name, "group".id as publisher_id, "group".name as publisher_name, "group".title as publisher_title
        """
        sql += main_sql + " order by publisher_title"
    else:
        sql = 'select distinct "group".id as publisher_id, "group".name as publisher_name, "group".title as publisher_title' + main_sql + " order by publisher_title "
    rows = model.Session.execute(sql, values).fetchall()
    if organisation_name or include_resources:
        data = [] # list of resource dicts with the addition of openness score info
        for row in rows:
            resource = DictObj(url=row.url, openness_score='0',
                               openness_score_reason=row.reason)
            #Would be good to add in openness_score_failure_count too, maybe like this:
            # task_data = {'entity_id': resource['id'], 'task_type': 'qa', 'openness_score_failure_count': key}
            # status = p.toolkit.get_action('task_status_show')(context, task_data)
            # resource[key] = status.get('value')
            data.append([row.name, row.title, row.publisher_name, row.publisher_title, resource])
        # This is a dictionary with the keys being the (organisation_name, id) pairs)
        return _collapse(data, [_extract_publisher, _extract_dataset])
    else:
        result = {}
        for row in rows:
            pub_title, pub_name = row.publisher_title, row.publisher_name
            result[(pub_title, pub_name)] = None
        return result

not_broken_but_0_stars = set(('Chose not to download'))

def broken_resource_links_by_dataset_for_organisation_detailed(organisation_name):
    '''
    Returns a dictionary detailing broken resource links for the organisation

    i.e.:
    {'publisher_name': 'cabinet-office',
     'publisher_title:': 'Cabinet Office',
     'broken_resources': [
       {'package_name', 'package_title', 'resource_url', 'reason', 'count', 'first_broken'}
      ...]

    '''
    values = {}
    sql = """
        select package.id as package_id,
               task_status.key as task_status_key,
               task_status.value as task_status_value,
               task_status.last_updated as task_status_last_updated,
               resource.id as resource_id,
               resource.url as resource_url,
               resource.position,
               package.title as package_title,
               package.name as package_name,
               "group".id as publisher_id,
               "group".name as publisher_name,
               "group".title as publisher_title
        from task_status 
            left join resource on task_status.entity_id = resource.id
            left join resource_group on resource.resource_group_id = resource_group.id
            left join package on resource_group.package_id = package.id
            left join member on member.table_id = package.id
            left join "group" on member.group_id = "group".id
        where 
            entity_id in (select entity_id from task_status where task_status.key='openness_score' and value='0')
            and package.state = 'active'
            and resource.state='active'
            and resource_group.state='active'
            and "group".state='active'
            and "group".name = :org_name
        order by package.title, package.name, resource.position
        """
    values['org_name'] = organisation_name
    rows = model.Session.execute(sql, values)

    data = [] # list of resource dicts with the addition of openness score info
    last_row = None
    # each resource has a few rows of task_status properties, so collate these
    def save_res_data(row, res_data, data):
        if res_data['openness_score_reason'] in not_broken_but_0_stars:
            # ignore row
            return
        data.append(res_data)
    def init_res_data(row):
        res_data = OrderedDict()
        res_data['package_name'] = row.package_name
        res_data['package_title'] = row.package_title
        res_data['resource_id'] = row.resource_id
        res_data['resource_url'] = row.resource_url
        res_data['resource_position'] = row.position
        return res_data
    res_data = None
    for row in rows:
        if not last_row:
            res_data = init_res_data(row)
        elif row.resource_id != last_row.resource_id and res_data:
            save_res_data(last_row, res_data, data)
            res_data = init_res_data(row)
        res_data[row.task_status_key] = row.task_status_value
        if 'openness_score_updated' in res_data:
            res_data['openness_score_updated'] = max(row.task_status_last_updated,
                                                     res_data['openness_score_updated'])
        else:
            res_data['openness_score_updated'] = row.task_status_last_updated
        last_row = row
    if res_data:
        save_res_data(row, res_data, data)    

    return {'publisher_name': row.publisher_name if data else organisation_name,
            'publisher_title': row.publisher_title if data else '',
            'broken_resources': data}

def _collapser(data, key_func=None):
    result = {}
    for row in data:
        if key_func:
            row = key_func(row)
        if row is None:
            raise Exception(key_func)
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
    Each row should be a list of the form [name, title, publisher_name, publisher_title, Resource]

    Returns a list of the form:

        [(publisher.title, publisher.name), row[0], row[1], row[4]]
    """
    name, title, publisher_name, publisher_title, resource = row
    return [(publisher_title, publisher_name), name, title, resource]

def _extract_dataset(row):
    """
    Extract dataset info from a query result row.
    Each row should be a list of the form [name, title, Resource]

    Returns a list of the form:

        [(name, title), Resource]
    """
    return [(row[0], row[1]), row[2]]

