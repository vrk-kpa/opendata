try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import json
import csv
from ckanext.qa.reports import (
    five_stars,
    resource_five_stars,
    broken_resource_links_by_dataset,
    broken_resource_links_by_dataset_for_organisation,
    organisations_with_broken_resource_links,
    organisations_with_broken_resource_links_by_name,
)
from pylons import config

import ckan.plugins as p
from ckan.lib.base import BaseController, response


c = p.toolkit.c
render = p.toolkit.render

class QAController(BaseController):

    def index(self):
        c.organisations = p.toolkit.asbool(config.get('qa.organisations', True))
        return render('qa/index.html')

    def package_index(self):
        return render('qa/datasets.html')

    def five_stars(self):
        c.packages = five_stars()
        return p.toolkit.render('qa/five_stars.html')

    def dataset_broken_resource_links(self):
        c.packages = broken_resource_links_by_dataset()
        return render('qa/dataset_broken_resource_links.html')

    def organisation_index(self):
        return render('qa/organisations.html')

    def broken_resource_links(self, id=None):
        if id is None:
            c.organisations = organisations_with_broken_resource_links_by_name()
            return render('qa/organisation_broken_resource_links.html')
        else:
            c.id = id
            c.organisation = broken_resource_links_by_dataset_for_organisation(organisation_id=id)
            return render('qa/broken_resource_links_for_organisation.html')

    headers = [
        'Organisation Name',
        'Organisation ID',
        'Dataset Name',
        'Dataset ID',
        'Resource URL',
        'Resource Score',
        'Resource Score Reason',
    ]

    def resource_five_stars(self, id):
        result = resource_five_stars(id)
        return self._output_json(result)

    def dataset_five_stars(self, id=None):
        result = five_stars(id)
        return self._output_json(result)

    def broken_resource_links_by_dataset(self, format='json'):
        result = broken_resource_links_by_dataset()
        if format == 'csv':
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
            filename = 'broken_links_by_dataset'
            return  self._output_csv_file(self.headers[2:], rows, filename)
        else:
            return self._output_json(result)

    def organisations_with_broken_resource_links(self, id, format='json'):
        result = organisations_with_broken_resource_links()
        if format == 'csv':
            rows = []
            for organisation, datasets in result.items():
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
            return  self._output_csv_file(self.headers, rows, id)
        else:
            return self._output_json(result)

    def broken_resource_links_by_dataset_for_organisation(self, id, format='json'):
        result = broken_resource_links_by_dataset_for_organisation(id)
        if format == 'csv':
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
            return  self._output_csv_file(self.headers, rows, id)
        else:
            return self._output_json(result)

    def _output_json(self, data):
        response.headers['Content-Type'] = 'application/json'
        return json.dumps(data)

    def _output_csv_file(self, headers, rows, filename):
        filename = '%s.csv' % filename
        response.headers['Content-Type'] = 'application/csv'
        response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
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
