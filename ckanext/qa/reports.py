import datetime
import re
from collections import namedtuple, defaultdict

from sqlalchemy.util import OrderedDict
from sqlalchemy import or_, and_, func

import ckan.model as model
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.helpers import json
from ckan.lib.search.query import PackageSearchQuery
from ckanext.dgu.lib.publisher import go_down_tree, go_up_tree
from ckan.lib.base import abort

import logging

log = logging.getLogger(__name__)

resource_dictize = model_dictize.resource_dictize

def convert_sqlalchemy_result_to_DictObj(result):
    return DictObj(zip(result.keys(), result))

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

def dataset_five_stars(dataset_id):
    '''For a dataset, return an overall five star score plus textual details of
    why it merits that.
    Of the resources, it returns details of the one with the highest QA score.
    Returns a dict of {'name': <package name>,
                       'title': <package title>,
                       'id': <resource id>,
                       'last_updated': <date of last update of openness score
                                        (datetime)>,
                       'value': <openness score (int)>,
                       'reason': <text describing score reasoning>}
    '''

    from sqlalchemy.sql.expression import desc
    import ckan.model as model
    # Run a query to choose the most recent, highest qa score of all resources in this dataset.
    query = model.Session.query(model.Package.name, model.Package.title, model.Resource.id, model.TaskStatus.last_updated.label('last_updated'), model.TaskStatus.value.label('value'),)\
        .join(model.ResourceGroup, model.Package.id == model.ResourceGroup.package_id)\
        .join(model.Resource)\
        .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
        .filter(model.TaskStatus.key==u'openness_score')\
        .filter(model.Package.id == dataset_id)\
        .filter(model.Resource.state==u'active')\
        .order_by(desc(model.TaskStatus.value))\
        .order_by(desc(model.TaskStatus.last_updated))\

    report = query.first()
    if not report:
        return None

    # Transfer to a DictObj - I don't trust the SqlAlchemy result to
    # exist for the remainder of the request, although it's not disappeared
    # in practice.
    result = convert_sqlalchemy_result_to_DictObj(report)
    result['value'] = int(report.value)

    # Get openness_reason for the score on that resource on that date
    query = model.Session.query(model.Resource.id, model.TaskStatus.last_updated.label('last_updated'), model.TaskStatus.value.label('value'),)\
        .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
        .filter(model.TaskStatus.key == u'openness_score_reason')\
        .filter(model.Resource.id == report.id)\
        .order_by(desc(model.TaskStatus.last_updated))
    reason_result = query.first()
    openness_score_reason = query.first().value if reason_result else 'Not yet available'
    result['reason'] = openness_score_reason

    return result

def resource_five_stars(id):
    """
    Return a dict containing the QA results for a given resource

    Each dict is of the form:
        {'openness_score': <int>,
         'openness_score_reason': <string>,
         'openness_update': <datetime>}
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

        last_updated_datestamp = max(
            openness_score_updated,
            openness_score_reason_updated)
        last_updated = datetime.datetime(*map(int, re.split('[^\d]', last_updated_datestamp)[:-1]))

        result = {
            'openness_score': openness_score,
            'openness_score_reason': openness_score_reason,
            'openness_updated': last_updated
        }
    except p.toolkit.ObjectNotFound:
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

def organisations_with_broken_resource_links_by_name():
    result = _get_broken_resource_links().keys()
    result.sort()
    return result

def organisations_with_broken_resource_links(include_resources=False):
    return _get_broken_resource_links(include_resources=include_resources)


not_broken_but_0_stars = set(('Chose not to download',))
archiver_status__not_broken_link = set(('Chose not to download', 'Archived successfully'))

def organisation_score_summaries(include_sub_organisations=False):
    '''Returns a list of all organisations with a summary of scores.
    Does SOLR query to be quicker.
    '''
    publisher_scores = []
    for publisher in model.Group.all(group_type='publisher'):
        if include_sub_organisations:
            q = 'parent_publishers:%s' % publisher.name
        else:
            q = 'publisher:%s' % publisher.name
        query = {
            'q': q,
            'facet': 'true',
            'facet.mincount': 1,
            'facet.limit': 10,
            'facet.field': ['openness_score'],
            'rows': 0,
            }
        solr_searcher = PackageSearchQuery()
        dataset_result = solr_searcher.run(query)
        score = solr_searcher.facets['openness_score']
        publisher_score = OrderedDict((
            ('publisher_title', publisher.title),
            ('publisher_name', publisher.name),
            ('dataset_count', dataset_result['count']),
            ('TBC', score.get('-1', 0)),
            (0, score.get('0', 0)),
            (1, score.get('1', 0)),
            (2, score.get('2', 0)),
            (3, score.get('3', 0)),
            (4, score.get('4', 0)),
            (5, score.get('5', 0)),
            ))
        publisher_score['total_stars'] = sum([(score.get(str(i), 0) * i) for i in range(6)])
        publisher_score['average_stars'] = float(publisher_score['total_stars']) / publisher_score['dataset_count'] if publisher_score['dataset_count'] else 0
        publisher_scores.append(publisher_score)
    return sorted(publisher_scores, key=lambda x: -x['total_stars'])

def scores_by_dataset_for_organisation(organisation_name):
    '''
    Returns a dictionary detailing openness scores for the organisation

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
            entity_id in (select entity_id from task_status where task_status.task_type='archiver' and task_status.key='status' and value='0')
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

def organisations_with_broken_resource_links(include_sub_organisations=False):
    # get list of orgs that themselves have broken links
    sql = """
        select count(distinct(package.id)) as broken_package_count,
               count(resource.id) as broken_resource_count,
               "group".name as publisher_name,
               "group".title as publisher_title
        from task_status 
            left join resource on task_status.entity_id = resource.id
            left join resource_group on resource.resource_group_id = resource_group.id
            left join package on resource_group.package_id = package.id
            left join member on member.table_id = package.id
            left join "group" on member.group_id = "group".id
        where 
            entity_id in (select entity_id from task_status where task_status.task_type='archiver' and task_status.key='status' and %(status_filter)s)
            and task_status.key='status'
            and package.state = 'active'
            and resource.state='active'
            and resource_group.state='active'
            and "group".state='active'
        group by "group".name, "group".title
        order by "group".title;
        """ % {
        'status_filter': ' and '.join(["task_status.value!='%s'" % status for status in archiver_status__not_broken_link]),
        }
    rows = model.Session.execute(sql)
    if not include_sub_organisations:
        # need to convert to dict, since the sql results will disappear on return
        data = []
        for row in rows:
            row_data = OrderedDict((
                ('publisher_title', row.publisher_title),
                ('publisher_name', row.publisher_name),
                ('broken_package_count', row.broken_package_count),
                ('broken_resource_count', row.broken_resource_count),
                ))
            data.append(row_data)
    else:
        counts_by_publisher = {}
        for row in rows:
            for publisher in go_up_tree(model.Group.by_name(row.publisher_name)):
                if publisher not in counts_by_publisher:
                    counts_by_publisher[publisher] = [0, 0]
                counts_by_publisher[publisher][0] += row.broken_package_count
                counts_by_publisher[publisher][1] += row.broken_resource_count
            
        data = []
        for row in sorted(counts_by_publisher.items(), key=lambda x: x[0].title):
            row_data = OrderedDict((
                ('publisher_title', row[0].title),
                ('publisher_name', row[0].name),
                ('broken_package_count', row[1][0]),
                ('broken_resource_count', row[1][1]),
                ))
            data.append(row_data)
    return data

def broken_resource_links_for_organisation(organisation_name,
                                           include_sub_organisations=False):
    '''
    Returns a dictionary detailing broken resource links for the organisation

    i.e.:
    {'publisher_name': 'cabinet-office',
     'publisher_title:': 'Cabinet Office',
     'data': [
       {'package_name', 'package_title', 'resource_url', 'status', 'reason', 'last_success', 'first_failure', 'failure_count', 'last_updated'}
      ...]

    '''
    values = {}
    sql = """
        select package.id as package_id,
               task_status.key as task_status_key,
               task_status.value as task_status_value,
               task_status.error as task_status_error,
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
            entity_id in (select entity_id from task_status where task_status.task_type='archiver' and task_status.key='status' and %(status_filter)s)
            and task_status.key='status'
            and package.state = 'active'
            and resource.state='active'
            and resource_group.state='active'
            and "group".state='active'
            %(org_filter)s
        order by package.title, package.name, resource.position
        """
    sql_options = {
        'status_filter': ' and '.join(["task_status.value!='%s'" % status for status in archiver_status__not_broken_link]),
        }
    org = model.Group.by_name(organisation_name)
    if not org:
        abort(404, 'Publisher not found')
    if not include_sub_organisations:
        sql_options['org_filter'] = 'and "group".name = :org_name'
        values['org_name'] = organisation_name
    else:
        sub_org_filters = ['"group".name=\'%s\'' % org.name for org in go_down_tree(org)]
        sql_options['org_filter'] = 'and (%s)' % ' or '.join(sub_org_filters)

    item_properties_as_dates = set(('first_failure', 'last_success'))
    rows = model.Session.execute(sql % sql_options, values)
    data = []
    for row in rows:
        row_data = OrderedDict((
            ('dataset_title', row.package_title),
            ('dataset_name', row.package_name),
            ('publisher_title', row.publisher_title),
            ('publisher_name', row.publisher_name),
            ('resource_position', row.position),
            ('resource_id', row.resource_id),
            ('resource_url', row.resource_url),
            ('status', row.task_status_value),
            ))
        if row.task_status_error:
            item_properties = json.loads(row.task_status_error)
            for key, value in item_properties.items():
                if key in item_properties_as_dates:
                    row_data[key] = datetime.datetime(*map(int, re.split('[^\d]', value)[:-1])) \
                                    if value else None
                else:
                    row_data[key] = value
        row_data['last_updated'] = row.task_status_last_updated
        data.append(row_data)

    organisation_title = org.title

    return {'publisher_name': organisation_name,
            'publisher_title': organisation_title,
            'data': data}

def organisation_dataset_scores(organisation_name,
                                include_sub_organisations=False):
    '''
    Returns a dictionary detailing dataset openness scores for the organisation

    i.e.:
    {'publisher_name': 'cabinet-office',
     'publisher_title:': 'Cabinet Office',
     'data': [
       {'package_name', 'package_title', 'resource_url', 'score', 'reason', 'last_updated'}
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
        from resource
            left join task_status on task_status.entity_id = resource.id
            left join resource_group on resource.resource_group_id = resource_group.id
            left join package on resource_group.package_id = package.id
            left join member on member.table_id = package.id
            left join "group" on member.group_id = "group".id
        where 
            entity_id in (select entity_id from task_status where task_status.task_type='qa')
            and package.state = 'active'
            and resource.state='active'
            and resource_group.state='active'
            and "group".state='active'
            %(org_filter)s
        order by package.title, package.name, resource.position, task_status.key
        """
    sql_options = {}
    org = model.Group.by_name(organisation_name)
    if not org:
        abort(404, 'Publisher not found')

    if not include_sub_organisations:
        sql_options['org_filter'] = 'and "group".name = :org_name'
        values['org_name'] = organisation_name
    else:
        sub_org_filters = ['"group".name=\'%s\'' % org.name for org in go_down_tree(org)]
        sql_options['org_filter'] = 'and (%s)' % ' or '.join(sub_org_filters)

    rows = model.Session.execute(sql % sql_options, values)
    data = {} # dataset_name: {properties}
    for row in rows:
        package_data = data.get(row.package_name)
        if not package_data:
            package_data = OrderedDict((
                ('dataset_title', row.package_title),
                ('dataset_name', row.package_name),
                ('publisher_title', row.publisher_title),
                ('publisher_name', row.publisher_name),
                # the rest are placeholders to hold the details
                # of the highest scoring resource
                ('resource_position', None),
                ('resource_id', None),
                ('resource_url', None),
                ('openness_score', None),
                ('openness_score_reason', None),
                ('last_updated', None),
                ))
        if row.task_status_key == 'openness_score' and \
           (not package_data['openness_score'] or \
            row.task_status_value > package_data['openness_score']):
            package_data['resource_position'] = row.position
            package_data['resource_id'] = row.resource_id
            package_data['resource_url'] = row.resource_url
            package_data['openness_score'] = row.task_status_value
            package_data['openness_score_reason'] = None # filled in next row
            package_data['last_updated'] = row.task_status_last_updated
        elif row.task_status_key == 'openness_score_reason' and \
             package_data['resource_id'] == row.resource_id:
            package_data['openness_score_reason'] = row.task_status_value

        data[row.package_name] = package_data

    organisation_title = org.title

    return {'publisher_name': organisation_name,
            'publisher_title': organisation_title,
            'data': data.values()}
