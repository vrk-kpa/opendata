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
from ..dictization import (
    five_stars,
    broken_resource_links_by_package,
    broken_resource_links_by_package_for_organisation, 
    organisations_with_broken_resource_links,
)
from ckanext.qa.lib.db import get_resource_result
from base import QAController

headers = [
    'Organisation Name',
    'Organisation ID',
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
                
    def package_five_stars(self):
        return json.dumps(five_stars())
        
    def broken_resource_links_by_package(self, format='json'):
        result = broken_resource_links_by_package()
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for package, resources in result:
                for resource in resources:
                    row = [
                        package[0],
                        package[1],
                        resource.url,
                        unicode(resource.extras.get('openness_score')),
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
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for organisation, packages in result.items():
                for package, resources in packages.items():
                    for resource in resources:
                        row = [
                            organisation[0],
                            unicode(organisation[1]),
                            package[0],
                            package[1],
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

    def broken_resource_links_by_package_for_organisation(self, id, format='json'):
        result = broken_resource_links_by_package_for_organisation(id)
        if format == 'csv':
            filename = '%s.csv' % (id)
            response.headers['Content-Type'] = 'application/csv'
            response.headers['Content-Disposition'] = str('attachment; filename=%s' % (filename))
            rows = []
            for package, resources in result['packages'].items():
                for resource in resources:
                    row = [
                        result['title'], 
                        unicode(result['id']), 
                        package[0],
                        package[1],
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

    @jsonify
    def resources_available(self, id):
        """
        Looks at the QA results for each resource in the package identified by id.
        Returns a JSON object of the form:
            
            {'resources' : [<list of resource objects>]}

        Each resource object is of the form:

            {'resource_available': 'true|false', 'resource_hash': '<value>',
             'resource_cache': '<value>'}
        """
        context = {'model': model, 'id': id, 'user': c.user or c.author}
        pkg = get.package_show(context)

        if not pkg:
            abort(404, _('Package not found'))

        archive_folder = os.path.join(config['ckan.qa_archive'], 'downloads')
        archive_file = os.path.join(archive_folder, 'archive.db')
        if not os.path.exists(archive_file):
            return {'error': 'no archive file found, cannot check resource availabilty'}

        resources = []
        for resource in pkg.get('resources', []):
            r = {}
            r['resource_hash'] = resource[u'hash']
            r['resource_available'] = 'unknown'
            r['resource_cache'] = ''
            # look at archive results to see if resource was found
            archive_result = get_resource_result(archive_file, resource[u'id'])
            if archive_result:
                if archive_result['success'] == u'True':
                    r['resource_available'] = 'true'
                else:
                    r['resource_available'] = 'false'
                    # see if we have a saved copy
                    cache = os.path.join(archive_folder, pkg[u'name'])
                    # TODO: update this to handle other formats
                    #       save extension info in archive file
                    cache = os.path.join(cache, resource[u'hash'] + '.csv')
                    if os.path.exists(cache):
                        # create the url to serve this copy
                        webstore = config.get('ckan.webstore_url', 'http://test-webstore.ckan.net')
                        r['resource_cache'] = webstore + '/downloads/' + \
                            pkg[u'name'] + '/' + resource[u'hash'] + '.csv'
            # add to resource list
            resources.append(r)
        return {'resources': resources}
