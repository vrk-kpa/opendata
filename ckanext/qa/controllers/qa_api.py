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

class ApiController(BaseController):
                
    def package_five_stars(self):
        return json.dumps(five_stars())
        
    def broken_resource_links_by_package(self):
        return json.dumps(broken_resource_links_by_package())

    def broken_resource_links_by_package_for_organisation(self, id, format='json'):
        result = broken_resource_links_by_package_for_organisation(id)
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=%s' % (filename)
            csvout = StringIO.StringIO()
            csvwriter = csv.writer(
                csvout,
                dialect='excel',
                quoting=csv.QUOTE_NONNUMERIC
            )
            csvwriter.writerow([
                'organisation_name',
                'organisation_id',
                #'published_by',
                #'published_via',
                'package_name',
                'package_id',
                'resource_url',
                'resource_score',
                'resource_score_reason',
            ])
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
                    csvwriter.writerow(row)
            csvout.seek(0)
            return csvout.read()
        else:
            return json.dumps(result)

