import datetime
import re
import os
import collections
from collections import namedtuple, defaultdict

from sqlalchemy.util import OrderedDict
from sqlalchemy import or_, and_, func
from sqlalchemy.sql.expression import desc

import ckan.model as model
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.helpers import json, OrderedDict
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
                       'reason': <text describing score reasoning>,
                       'is_broken': <whether the link is broken (bool)>,
                       'format': <the detected file format>,
                       }
    '''


    import ckan.model as model
    # Run a query to choose the most recent, highest qa score of all resources in this dataset.
    query = model.Session.query(model.Package.name, model.Package.title, model.Resource.id, model.TaskStatus.last_updated.label('last_updated'), model.TaskStatus.value.label('value'), model.TaskStatus.error.label('error'))\
        .join(model.ResourceGroup, model.Package.id == model.ResourceGroup.package_id)\
        .join(model.Resource)\
        .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
        .filter(model.TaskStatus.task_type==u'qa')\
        .filter(model.TaskStatus.key==u'status')\
        .filter(model.Package.id == dataset_id)\
        .filter(model.Resource.state==u'active')\
        .order_by(desc(model.TaskStatus.value))\
        .order_by(desc(model.TaskStatus.last_updated))\

    report = query.first()
    if not report:
        pkg = model.Package.get(dataset_id)
        if pkg:
            num_resources = model.Session.query(model.ResourceGroup)\
                            .join(model.Resource)\
                            .filter(model.ResourceGroup.package_id == dataset_id)\
                            .filter(model.Resource.state==u'active')\
                            .count()
            if num_resources == 0:
                # Package has no resources, so gets 0 stars
                return {'name': pkg.name,
                        'title': pkg.title,
                        'id': None,
                        'last_updated': None,
                        'value': 0,
                        'reason': 'No data resources, so scores 0.'}
        # Package hasn't been rated yet
        return None

    # Transfer to a DictObj - I don't trust the SqlAlchemy result to
    # exist for the remainder of the request, although it's not disappeared
    # in practice.
    result = convert_sqlalchemy_result_to_DictObj(report)
    result['value'] = int(report.value)
    try:
        result.update(json.loads(result['error']))
    except ValueError, e:
        log.error('QA status "error" should have been in JSON format, but found: "%s" %s', result['error'], e)
        result['reason'] = 'Could not display reason due to a system error'
    del result['error']

    return result

def resource_five_stars(id):
    """
    Return a dict containing the QA results for a given resource

    Each dict is of the form:
    Returns a dict of {'name': <package name>,
                       'title': <package title>,
                       'id': <resource id>,
                       'last_updated': <date of last update of openness score
                                        (datetime)>,
                       'value': <openness score (int)>,
                       'reason': <text describing score reasoning>,
                       'is_broken': <whether the link is broken (bool)>,
                       'format': <the detected file format>,
                       'url_redirected_to': <url (str or null)>
                       }

      And for the time being it also keeps these deprecated keys:
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
        data['key'] = 'status'
        result = p.toolkit.get_action('task_status_show')(context, data)
        result['value'] = int(result['value'])
        result['last_updated'] = datetime.datetime(*map(int, re.split('[^\d]', result['last_updated'])[:-1]))

        try:
            result.update(json.loads(result['error']))
        except ValueError, e:
            log.error('QA status "error" should have been in JSON format, but found: "%s" %s', result['error'], e)
            result['reason'] = 'Could not display reason due to a system error'
        del result['error']

        # deprecated keys
        result['openness_score'] = result['value']
        result['openness_score_reason'] = result['reason']
        result['openness_updated'] = result['last_updated']

    except p.toolkit.ObjectNotFound:
        result = {}

    return result

def _find_in_cache(entity, key_root, withsub=False):
    key = key_root

    if withsub:
       key = "".join([key_root, '-withsub'])

    cache = model.DataCache.get_fresh(entity, key)
    if cache:
       log.debug("Found %s/%s in cache" % (entity,key_root,))
       return cache

    return None


def broken_resource_links_by_dataset():
    """
    Return a list of named tuples, one for each dataset that contains
    broken resource links (defined as resources with an openness score of 0
    and the reason is an invalid URL, 404, timeout or similar, as opposed
    to it being too big to archive or system errors during archival).

    The named tuple (for each dataset) is of the form:
        (name (str), title (str), resources (list of dicts))
    """
    q = model.Session.query(model.Package.name, model.Package.title, model.Resource.id, model.Resource.url, model.TaskStatus.last_updated.label('last_updated'), model.TaskStatus.value.label('value'), model.TaskStatus.error.label('error'))\
        .join(model.ResourceGroup, model.Package.id == model.ResourceGroup.package_id)\
        .join(model.Resource)\
        .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
        .filter(model.TaskStatus.task_type==u'qa')\
        .filter(model.TaskStatus.key==u'status')\
        .filter(model.TaskStatus.error.like('%"is_broken": true%'))\
        .filter(model.Resource.state==u'active')\
        .filter(model.Package.state==u'active')\
        .order_by(desc(model.TaskStatus.value))\
        .order_by(desc(model.TaskStatus.last_updated))
    rows = q.all()
    # One row per resource, therefore need to collate them by dataset
    datasets = OrderedDict()
    for row in rows:
        openness_details = json.loads(row.error)
        res = DictObj(url=row.url,
                      openness_score_reason=openness_details.get('reason'))
        if row.name in datasets:
            datasets[row.name].resources.append(res)
        else:
            datasets[row.name] = DictObj(name=row.name,
                                         title=row.title,
                                         resources=[res])
    return datasets.values()


# NOT USED in this branch, but is used in release-v2.0
def organisations_with_broken_resource_links_by_name():
    raise NotImplementedError

# NOT USED in this branch, but is used in release-v2.0
def organisations_with_broken_resource_links(include_resources=False):
    raise NotImplementedError


not_broken_but_0_stars = set(('Chose not to download',))
archiver_status__not_broken_link = set(('Chose not to download', 'Archived successfully'))

def organisation_score_summaries(include_sub_organisations=False, use_cache=True):
    '''Returns a list of all organisations with a summary of scores.
    Does SOLR query to be quicker.
    '''

    if use_cache:
        val = _find_in_cache("__all__",'organisation_score_summaries', withsub=include_sub_organisations)
        if val:
            return val

    publisher_scores = []
    for publisher in model.Group.all(group_type='organization'):
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
            ('0', score.get('0', 0)),
            ('1', score.get('1', 0)),
            ('2', score.get('2', 0)),
            ('3', score.get('3', 0)),
            ('4', score.get('4', 0)),
            ('5', score.get('5', 0)),
            ))
        publisher_score['total_stars'] = sum([(score.get(str(i), 0) * i) for i in range(6)])
        publisher_score['average_stars'] = float(publisher_score['total_stars']) / publisher_score['dataset_count'] if publisher_score['dataset_count'] else 0
        publisher_scores.append(publisher_score)
    return sorted(publisher_scores, key=lambda x: -x['total_stars'])


def organisations_with_broken_resource_links(include_sub_organisations=False, use_cache=True):
    # get list of orgs that themselves have broken links
    if use_cache:
        val = _find_in_cache("__all__",'organisations_with_broken_resource_links', withsub=include_sub_organisations)
        if val:
            return val

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
            and task_status.task_type='qa'
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
                                           include_sub_organisations=False,
                                           use_cache=True):
    '''
    Returns a dictionary detailing broken resource links for the organisation

    i.e.:
    {'publisher_name': 'cabinet-office',
     'publisher_title:': 'Cabinet Office',
     'data': [
       {'package_name', 'package_title', 'resource_url', 'status', 'reason', 'last_success', 'first_failure', 'failure_count', 'last_updated'}
      ...]

    '''
    if use_cache:
        val = _find_in_cache(organisation_name, 'broken-link-report', withsub=include_sub_organisations)
        if val:
            return val

    ## This was the start of a trial - left in case it was useful
    ## q = model.Session.query(model.Package.name, model.Package.title, model.Resource.id, model.Resource.url, model.TaskStatus.last_updated.label('last_updated'), model.TaskStatus.value.label('value'), model.TaskStatus.error.label('error'), model.Group.id.label('publisher_id'), model.Group.name.label('publisher_name'), model.Group.title.label('publisher_title'))\
    ##     .join(model.ResourceGroup, model.Package.id == model.ResourceGroup.package_id)\
    ##     .join(model.Resource)\
    ##     .join(model.TaskStatus, model.TaskStatus.entity_id == model.Resource.id)\
    ##     .join(model.Member, model.Member.table_id == model.Package.id)\
    ##     .join(model.Group)\
    ##     .filter(model.TaskStatus.task_type==u'qa')\
    ##     .filter(model.TaskStatus.key==u'status')\
    ##     .filter(model.TaskStatus.error.like('%"is_broken": true%'))\
    ##     .filter(model.Resource.state==u'active')\
    ##     .filter(model.Package.state==u'active')\
    ##     .filter(model.Group.name==organisation_name)\
    ##     .filter(model.Group.state==u'active')\
    ##     .order_by(desc(model.TaskStatus.value))\
    ##     .order_by(desc(model.TaskStatus.last_updated))
    ## rows = q.all()
    ## print rows[:1]

    ## data = {}
    ## for row in rows:
    ##     pass

    ## return {'publisher_name': row.publisher_name if data else organisation_name,
    ##         'publisher_title': row.publisher_title if data else '',
    ##         'data': data}

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
               "group".title as publisher_title,
               package_extra.value as external_reference
        from task_status
            left join resource on task_status.entity_id = resource.id
            left join resource_group on resource.resource_group_id = resource_group.id
            left join package on resource_group.package_id = package.id
            left join member on member.table_id = package.id
            left join "group" on member.group_id = "group".id
            left join package_extra on package_extra.package_id = package.id
        where
            entity_id in (select entity_id from task_status where task_status.task_type='archiver' and task_status.key='status' and %(status_filter)s)
            and task_status.task_type='archiver'
            and task_status.key='status'
            and package.state = 'active'
            and resource.state='active'
            and resource_group.state='active'
            and "package_extra".key='external_reference'
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
    organisation_title = org.title

    if not include_sub_organisations:
        sql_options['org_filter'] = 'and "group".name = :org_name'
        values['org_name'] = organisation_name
    else:
        sub_org_filters = ['"group".name=\'%s\'' % organisation.name for organisation in go_down_tree(org)]
        sql_options['org_filter'] = 'and (%s)' % ' or '.join(sub_org_filters)

    item_properties_as_dates = set(('first_failure', 'last_success'))
    rows = model.Session.execute(sql % sql_options, values)
    data = []
    for row in rows:
        via = ''
        if row.external_reference == 'ONSHUB':
            via = "Stats Hub"
        elif row.external_reference.startswith("DATA4NR"):
            via = "Data4nr"
        row_data = OrderedDict((
            ('dataset_title', row.package_title),
            ('dataset_name', row.package_name),
            ('publisher_title', row.publisher_title),
            ('publisher_name', row.publisher_name),
            ('resource_position', row.position),
            ('resource_id', row.resource_id),
            ('resource_url', row.resource_url),
            ('status', row.task_status_value),
            ('via', via)
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

    return {'publisher_name': organisation_name,
            'publisher_title': organisation_title,
            'data': data}

def organisation_dataset_scores(organisation_name,
                                include_sub_organisations=False,
                                use_cache=True):
    '''
    Returns a dictionary detailing openness scores for the organisation
    for each dataset.

    i.e.:
    {'publisher_name': 'cabinet-office',
     'publisher_title:': 'Cabinet Office',
     'data': [
       {'package_name', 'package_title', 'resource_url', 'openness_score', 'reason', 'last_updated', 'is_broken', 'format'}
      ...]

    NB the list does not contain datasets that have 0 resources and therefore
       score 0

    '''
    if use_cache:
        val = _find_in_cache(organisation_name, 'openness-report', withsub=include_sub_organisations)
        if val:
            return val

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
            and task_status.task_type='qa'
            and task_status.key='status'
            %(org_filter)s
        order by package.title, package.name, resource.position
        """
    sql_options = {}
    org = model.Group.by_name(organisation_name)
    if not org:
        abort(404, 'Publisher not found')
    organisation_title = org.title

    if not include_sub_organisations:
        sql_options['org_filter'] = 'and "group".name = :org_name'
        values['org_name'] = organisation_name
    else:
        sub_org_filters = ['"group".name=\'%s\'' % organisation.name for organisation in go_down_tree(org)]
        sql_options['org_filter'] = 'and (%s)' % ' or '.join(sub_org_filters)

    rows = model.Session.execute(sql % sql_options, values)
    data = dict() # dataset_name: {properties}
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
        if row.task_status_value > package_data['openness_score']:
            package_data['resource_position'] = row.position
            package_data['resource_id'] = row.resource_id
            package_data['resource_url'] = row.resource_url

            try:
                package_data.update(json.loads(row.task_status_error))
            except ValueError, e:
                log.error('QA status "error" should have been in JSON format, but found: "%s" %s', task_status_error, e)
                package_data['reason'] = 'Could not display reason due to a system error'

            package_data['openness_score'] = row.task_status_value
            package_data['openness_score_reason'] = package_data['reason'] # deprecated
            package_data['last_updated'] = row.task_status_last_updated

        data[row.package_name] = package_data

    # Sort the results by openness_score asc so we can see the worst
    # results first
    data = OrderedDict(sorted(data.iteritems(),
                       key=lambda x: x[1]['openness_score']))

    return {'publisher_name': organisation_name,
            'publisher_title': organisation_title,
            'data': data.values()}


def record_broken_link_totals(val, key):
    """
    'val' will be the result of calling organisations_with_broken_resource_links
    and we will use that data to work out how many broken links, and broken resources
    each publisher has and record it.  The report name 'key' will be used and the
    organisation stored in the entity_id for easy lookup.  The 'report' stored will be
    [date, broken_dataset_count, broken_resource_count]
    """
    import ckan.model as model

    log.info("Generating broken link totals for: {0}".format(key))

    # Check the date
    today = datetime.datetime.now().date()

    # Check for our DEBUG option to allow us to fake the date
    override_date_check = os.environ.get('OVERRIDE_DATE_CHECK', False)

    # Ideally check if there are any values for this month and if not then
    # we should run through the process. For now we will just run on the first
    # of the month
    if today.day != 1 and not override_date_check:
        log.info("Skipping totals as not first day of the month")
        return

    # for each organisation
    for publisher in val:
        # publisher is an ordered dict
        title = publisher['publisher_title']
        name = publisher['publisher_name']
        broken_pkgs = publisher['broken_package_count']
        broken_rscs = publisher['broken_resource_count']

        data = {
            'packages': broken_pkgs,
            'resources': broken_rscs
        }

        current = model.DataCache.get_fresh(name, key)
        if current:
            current = collections.OrderedDict(current)
        else:
            current = collections.OrderedDict()

        current[today.isoformat()] = data

        model.DataCache.set(name, key, json.dumps(current))


def cached_reports(reports_to_run=None):
    """
    Called via the ICachedReport plugin implemented in plugin.py
    for pre-filling the cache with data for use at runtime
    """
    from ckan.lib.json import DateTimeJsonEncoder

    local_reports = set(['broken-link-report', 'broken-link-report-withsub',
                        'openness-report', 'openness-report-withsub',
                        'organisation_score_summaries',
                        'organisations_with_broken_resource_links'])
    if reports_to_run:
        local_reports = set(reports_to_run) & local_reports

    if not local_reports:
        return

    publishers = model.Session.query(model.Group).\
       filter(model.Group.type=='organization').\
       filter(model.Group.state=='active')

    if "organisations_with_broken_resource_links" in local_reports:
        # When generating these reports, we have a special case where we
        # want to use the val returned to keep track of the monthly
        # count of broken datasets and resources. This will allow us to graph
        # them over time.

        log.info("Generating organisations with broken resource links overview")
        val = organisations_with_broken_resource_links(include_sub_organisations=False, use_cache=False)
        model.DataCache.set("__all__", "organisations_with_broken_resource_links", json.dumps(val,cls=DateTimeJsonEncoder))
        record_broken_link_totals(val, 'broken-link-totals')

        val = organisations_with_broken_resource_links(include_sub_organisations=True, use_cache=False)
        model.DataCache.set("__all__", "organisations_with_broken_resource_links-withsub", json.dumps(val,cls=DateTimeJsonEncoder))
        record_broken_link_totals(val, 'broken-link-totals-withsub')

    if 'organisation_score_summaries' in local_reports:
        log.info("Generating organisation score summaries overview")

        val = organisation_score_summaries(include_sub_organisations=False, use_cache=False)
        model.DataCache.set("__all__", "organisation_score_summaries", json.dumps(val,cls=DateTimeJsonEncoder))

        val = organisation_score_summaries(include_sub_organisations=True, use_cache=False)
        model.DataCache.set("__all__", "organisation_score_summaries-withsub", json.dumps(val,cls=DateTimeJsonEncoder))

    log.info("Fetching %d publishers" % publishers.count())

    for publisher in publishers.all():
        # Run the broken links report with and without include_sub_organisations set
        if 'broken-link-report' in local_reports:
            log.info("Generating broken link report for %s" % publisher.name)
            val = broken_resource_links_for_organisation(publisher.name, use_cache=False)
            model.DataCache.set(publisher.name, "broken-link-report", json.dumps(val,cls=DateTimeJsonEncoder))

        if 'broken-link-report-withsub' in local_reports:
            log.info("Generating broken link report for %s with sub-publishers" % publisher.name)
            val = broken_resource_links_for_organisation(publisher.name, include_sub_organisations=True, use_cache=False)
            model.DataCache.set(publisher.name, "broken-link-report-withsub", json.dumps(val,cls=DateTimeJsonEncoder))

        # Run the openness report with and without include_sub_organisations set
        if 'openness-report' in local_reports:
            log.info("Generating openness report for %s" % publisher.name)
            val = organisation_dataset_scores(publisher.name, use_cache=False)
            model.DataCache.set(publisher.name, "openness-report", json.dumps(val,cls=DateTimeJsonEncoder))

        if 'openness-report-withsub' in local_reports:
            log.info("Generating openness report for %s with sub-publishers" % publisher.name)
            val = organisation_dataset_scores(publisher.name, include_sub_organisations=True, use_cache=False)
            model.DataCache.set(publisher.name, "openness-report-withsub", json.dumps(val,cls=DateTimeJsonEncoder))

    model.Session.commit()
