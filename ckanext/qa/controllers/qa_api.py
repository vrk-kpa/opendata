import os
import json
import csv

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from pylons.decorators import jsonify
from pylons.i18n import _
from pylons import tmpl_context as c, config
from ckan import model
from ckan.logic.action import get
from ckan.lib.base import response, abort

from ckanext.qa.reports import (
    five_stars,
    broken_resource_links_by_dataset,
    broken_resource_links_by_dataset_for_organisation, 
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

def make_csv(result, headers, rows):
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
            items.append(item.encode('utf8'))
        try:
            csvwriter.writerow(items)
        except Exception, e:
            raise Exception("%s: %s, %s"%(e, row, items))
    csvout.seek(0)
    return csvout.read()

class ApiController(QAController):
                
    def dataset_five_stars(self):
        return json.dumps(five_stars())
        
    def broken_resource_links_by_dataset(self, format='json'):
        result = broken_resource_links_by_dataset()
        if format == 'csv':
            filename = '%s.csv' % (id)
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
                result,
                headers[2:],
                rows,
            )
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result)

    def organisations_with_broken_resource_links(self, id, format='json'):
        result = organisations_with_broken_resource_links()
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for organisation, datasets in result.items():
                for dataset, resources in datasets.items():
                    for resource in resources:
                        row = [
                            organisation[0],
                            unicode(organisation[1]),
                            dataset[0],
                            dataset[1],
                            resource.url,
                            unicode(resource.extras.get('openness_score')),
                            resource.extras.get('openness_score_reason'),
                        ]
                        rows.append(row)
            return make_csv(
                result,
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
            for dataset, resources in result['datasets'].items():
                for resource in resources:
                    row = [
                        result['title'], 
                        unicode(result['id']), 
                        dataset[0],
                        dataset[1],
                        resource.url,
                        unicode(resource.extras.get('openness_score')),
                        resource.extras.get('openness_score_reason'),
                    ]
                    rows.append(row)
            return make_csv(
                result,
                headers,
                rows,
            )
        else:
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(result)

