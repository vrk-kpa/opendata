try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import json
from ckan.lib.json import DateTimeJsonEncoder
import csv
import datetime

from ckan.lib.base import response, BaseController, request, abort
from ckanext.qa.reports import (
    dataset_five_stars,
    resource_five_stars,
    broken_resource_links_by_dataset,
    broken_resource_links_for_organisation,
    organisations_with_broken_resource_links,
    organisation_score_summaries,
    organisation_dataset_scores,
)
import ckan.plugins.toolkit as t

headers = [
    'Organisation Name',
    'Organisation ID',
    'Dataset Name',
    'Dataset ID',
    'Resource URL',
    'Resource Score',
    'Resource Score Reason',
]

def make_csv(headers, rows):
    csvout = StringIO.StringIO()
    csvwriter = csv.writer(
        csvout,
        dialect='excel',
        quoting=csv.QUOTE_NONNUMERIC
    )
    csvwriter.writerow(headers)
    for row in rows:
        items = []
        for item in row:
            if isinstance(item, datetime.datetime):
                item = item
            elif isinstance(item, int):
                item = unicode(item)
            else:
                item = item.encode('utf8')
            items.append(item)
        try:
            csvwriter.writerow(items)
        except Exception, e:
            raise Exception("%s: %s, %s"%(e, row, items))
    csvout.seek(0)
    return csvout.read()

def make_csv_from_dicts(rows):
    csvout = StringIO.StringIO()
    csvwriter = csv.writer(
        csvout,
        dialect='excel',
        quoting=csv.QUOTE_NONNUMERIC
    )
    # extract the headers by looking at all the rows and
    # get a full list of the keys, retaining their ordering
    headers_ordered = []
    headers_set = set()
    for row in rows:
        new_headers = set(row.keys()) - headers_set
        headers_set |= new_headers
        for header in row.keys():
            if header in new_headers:
                headers_ordered.append(header)
    csvwriter.writerow(headers_ordered)
    for row in rows:
        items = []
        for header in headers_ordered:
            item = row.get(header, 'no record')
            if isinstance(item, datetime.datetime):
                item = item.strftime('%Y-%m-%d %H:%M')
            elif isinstance(item, (int, long, float)):
                item = unicode(item)
            elif item is None:
                item = ''
            else:
                item = item.encode('utf8')
            items.append(item)
        try:
            csvwriter.writerow(items)
        except Exception, e:
            raise Exception("%s: %s, %s"%(e, row, items))
    csvout.seek(0)
    return csvout.read()

class ApiController(BaseController):

    def dataset_five_stars(self, id=None):
        if not id:
            abort(404)
        return json.dumps(dataset_five_stars(id), cls=DateTimeJsonEncoder)

    def resource_five_stars(self, id=None):
        if not id:
            abort(404)
        return json.dumps(resource_five_stars(id), cls=DateTimeJsonEncoder)

    def broken_resource_links_by_dataset(self, format='json'):
        result = broken_resource_links_by_dataset()
        if format == 'csv':
            filename = 'all_broken_links.csv'
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for dataset in result:
                for resource in dataset.resources:
                    row = [
                        dataset.name,
                        dataset.title,
                        resource.get('url', ''),
                        unicode(resource.get('openness_score', '')),
                        resource.get('openness_score_reason', ''),
                    ]
                    rows.append(row)
            return make_csv(
                headers[2:],
                rows,
            )
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result, cls=DateTimeJsonEncoder)

    def organisations_with_broken_resource_links(self, id=None, format='json'):
        include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        result = organisations_with_broken_resource_links(include_sub_organisations=include_sub_publishers)
        if format == 'csv':
            filename = 'broken_links%s.csv' % (('_' + id) if id else '')
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            return make_csv_from_dicts(result)
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result, cls=DateTimeJsonEncoder)

    def broken_resource_links_for_organisation(self, id=None, format='json'):
        if not id:
            abort(404)
        include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        result = broken_resource_links_for_organisation(id, include_sub_organisations=include_sub_publishers)['data']
        if format == 'csv':
            filename = 'broken_links_%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            return make_csv_from_dicts(result)
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result, cls=DateTimeJsonEncoder)

    def organisation_score_summaries(self, format='json'):
        include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        result = organisation_score_summaries(include_sub_organisations=include_sub_publishers)
        if format == 'csv':
            filename = 'organisations_by_dataset_scores.csv'
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            return make_csv_from_dicts(result)
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result, cls=DateTimeJsonEncoder)

    def organisation_dataset_scores(self, id=None, format='json'):
        if not id:
            abort(404)
        include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        result = organisation_dataset_scores(id, include_sub_organisations=include_sub_publishers)['data']
        if format == 'csv':
            filename = 'scores_%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            return make_csv_from_dicts(result)
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result, cls=DateTimeJsonEncoder)
