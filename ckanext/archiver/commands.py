from datetime import datetime
import json
import requests
import urlparse
from pylons import config
from pylons.test import pylonsapp
from paste.deploy import loadapp
import paste.fixture
import logging
import os
import paste
import pkg_resources

from ckan.lib.cli import CkanCommand

class Archiver(CkanCommand):
    """
    Download and save copies of all package resources.

    The result of each download attempt is saved to the CKAN task_status table, so the
    information can be used later for QA analysis.

    Usage:

        paster archiver update [{package-id}]
           - Archive all resources or just those belonging to a specific package 
             if a package id is provided

        paster archiver clean
            - Remove all archived resources
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 
    pkg_names = []

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.usage
            return

        cmd = self.args[0]
        self._load_config()

        from ckan.logic import get_action
        from ckan import model
        from ckan.model.types import make_uuid

        # Initialise logger after the config is loaded, so it is not disabled.
        self.log = logging.getLogger(__name__)

        #import after load config so CKAN_CONFIG evironment variable can be set
        import tasks
        user = get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})
        context = json.dumps({
            'site_url': config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'site_user_apikey': user.get('apikey'),
            'username': user.get('name'),
            'cache_url_root': config.get('ckan.cache_url_root')
        })
        api_url = '/api/action'

        # Setup a WSGI interface to CKAN to make requests to
        # to find the resource urls.
        # NB Before this was done using http requests, but that was
        # problematic for DGU - the request for the list of packages
        # took so long that Varnish returned 503. Best to do it in this process
        # and you save relying on site_url too.
        path = os.getcwd()
        pylonsapp = loadapp('config:' + self.filename,
                                       relative_to=path)
        wsgiapp = pylonsapp
        assert wsgiapp, 'Pylons load failed'
        app = paste.fixture.TestApp(wsgiapp)

        if cmd == 'update':
            if len(self.args) > 1:
                package_names = [self.args[1]]
            else:
                url = api_url + '/package_list'
                self.log.info('Requesting list of datasets from %r', url)
                response = app.post(url, "{}")
                self.log.info('List of datasets (status %s): %r...', response.status, response.body[:100])
                package_names = json.loads(response.body).get('result')

            self.log.info("Number of datasets to archive: %d" % len(package_names))

            for package_name in package_names:
                self.log.info('Getting dataset metadata: %s', package_name)

                # Get the dataset's resource urls
                data = json.dumps({'id': unicode(package_name)})
                response = app.post(api_url + '/package_show', data)
                package =  json.loads(response.body).get('result')

                self.log.info("Archival of dataset resource data added to celery queue: %s (%d resources)" % (package.get('name'), len(package.get('resources', []))))
                for resource in package.get('resources', []):
                    data = json.dumps(resource, {'model': model})
                    task_id = make_uuid()
                    archiver_task_status = {
                        'entity_id': resource['id'],
                        'entity_type': u'resource',
                        'task_type': u'archiver',
                        'key': u'celery_task_id',
                        'value': task_id,
                        'error': u'',
                        'last_updated': datetime.now().isoformat()
                    }
                    archiver_task_context = {
                        'model': model, 
                        'user': user.get('name')
                    }

                    get_action('task_status_update')(archiver_task_context, archiver_task_status)
                    tasks.update.apply_async(args=[context, data], task_id=task_id)

        elif cmd == 'clean':
            tasks.clean.delay()

        else:
            self.log.error('Command %s not recognized' % (cmd,))

