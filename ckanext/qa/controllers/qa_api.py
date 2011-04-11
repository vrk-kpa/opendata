import json
import csv

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from ckan.lib.base import BaseController, request, response, render
from ..dictization import (
    five_stars,
    broken_resource_links_by_package,
    broken_resource_links_by_package_for_organisation, 
    organisations_with_broken_resource_links,
)

headers = [
    'Organisation Name',
    'organisation ID',
    'Package Name',
    'Package ID',
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
        csvwriter.writerow(row)
    csvout.seek(0)
    return csvout.read()

class ApiController(BaseController):
                
    def package_five_stars(self):
        return json.dumps(five_stars())
        
    def broken_resource_links_by_package(self, format='json'):
        result = broken_resource_links_by_package()
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=%s' % (filename)
            rows = []
            for package, resources in result:
                for resource in resources:
                    row = [
                        package[0].encode('utf8'),
                        package[1].decode('utf8'),
                        resource.url,
                        resource.extras.get('openness_score'),
                        resource.extras.get('openness_score_reason'),
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
            response.headers['Content-Disposition'] = 'attachment; filename=%s' % (filename)
            rows = []
            for organisation, packages in result.items():
                for package, resources in packages.items():
                    for resource in resources:
                        row = [
                            organisation[0],
                            organisation[1],
                            package[0].encode('utf8'),
                            package[1].decode('utf8'),
                            resource.url,
                            resource.extras.get('openness_score'),
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

    def broken_resource_links_by_package_for_organisation(self, id, format='json'):
        result = broken_resource_links_by_package_for_organisation(id)
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=%s' % (filename)
            rows = []
            for package, resources in result['packages'].items():
                for resource in resources:
                    row = [
                        result['title'], 
                        result['id'], 
                        #package.get('published_by'),
                        #package.get('published_via'),
                        package[0].encode('utf8'),
                        package[1].decode('utf8'),
                        resource.url,
                        resource.extras.get('openness_score'),
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

