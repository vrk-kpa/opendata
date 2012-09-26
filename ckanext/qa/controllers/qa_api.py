try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import json
import csv
import datetime

from ckan.lib.base import response
from ckanext.qa.reports import (
    five_stars,
    resource_five_stars,
    broken_resource_links_by_dataset,
    broken_resource_links_by_dataset_for_organisation,
    broken_resource_links_by_dataset_for_organisation_detailed,
    organisations_with_broken_resource_links,
)
from base import QAController

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

class ApiController(QAController):

    def resource_five_stars(self, id):
        return json.dumps(resource_five_stars(id))
                
    def dataset_five_stars(self, id=None):
        return json.dumps(five_stars(id))
        
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
            return json.dumps(result)

    def organisations_with_broken_resource_links(self, id, format='json'):
        result = organisations_with_broken_resource_links(include_resources=True)
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            d = result.items()
            d.sort()
            for organisation, datasets in d:
                for dataset, resources in datasets.items():
                    for resource in resources:
                        row = [
                            organisation[0],
                            unicode(organisation[1]),
                            dataset[0],
                            dataset[1],
                            resource.get('url'),
                            unicode(resource.get('openness_score')),
                            resource.get('openness_score_reason'),
                        ]
                        rows.append(row)
            return make_csv(
                headers,
                rows,
            )
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result)

    def broken_resource_links_by_dataset_for_organisation(self, id, format='json'):
        result = broken_resource_links_by_dataset_for_organisation(id)
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for dataset, resources in result['packages'].items():
                for resource in resources:
                    row = [
                        result['title'], 
                        unicode(result['id']), 
                        dataset[0],
                        dataset[1],
                        resource.get('url'),
                        unicode(resource.get('openness_score')),
                        resource.get('openness_score_reason'),
                    ]
                    rows.append(row)
            return make_csv(
                headers,
                rows,
            )
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result)

    def broken_resource_links_by_dataset_for_organisation_detailed(self, id, format='json'):
        result = broken_resource_links_by_dataset_for_organisation_detailed(id)['broken_resources']
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            return make_csv_from_dicts(result)
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result)
