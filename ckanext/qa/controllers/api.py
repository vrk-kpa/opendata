import json
import csv

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from ckan.lib.base import BaseController, c, g, request, \
                          response, session, render, config, abort
from ..dictization import *

class ApiController(BaseController):
                
    def package_openness_scores(self, id=None):
        return json.dumps(package_openness_score(package_id=id))
        
    def packages_with_broken_resource_links(self, id=None, name=None):
        return json.dumps(packages_with_minimum_one_broken_resource(
            organization_id=id, organization_name=name
        ))

    def organizations_with_broken_resource_links(self, id, format='json'):
        packages = \
            packages_with_minimum_one_broken_resource(organization_id=id)
            
        if format == 'json':
            response.headers['Content-type'] = ''
            return json.dumps(orgs_with_broken_resource_links)
        elif format == 'csv':
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
                'organization_name',
                'organization_id',
                'published_by',
                'published_via',
                'package_name',
                'package_id',
                'resource_url',
                'resource_score',
                'resource_score_reason',
            ])
            
            for package in packages:
                for resource in package.get('resources'):
                    row = [
                        package.get('organization_name'),
                        package.get('organization_id'),
                        package.get('published_by'),
                        package.get('published_via'),
                        package.get('name'),
                        package.get('package_id'),
                        resource.get('url'),
                        resource.get('openness_score'),
                        resource.get('openness_score_reason'),
                    ]
                    csvwriter.writerow(row)
            csvout.seek(0)
            return csvout.read()