from datetime import datetime
import json
import requests
import urlparse
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.logic import get_action
from ckan import model
from ckan.model.types import make_uuid
import logging
logger = logging.getLogger()

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
            return

        cmd = self.args[0]
        self._load_config()
        #import after load config so CKAN_CONFIG evironment variable can be set
        import tasks
        user = get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})
        context = json.dumps({
            'site_url': config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'username': user.get('name'),
            'cache_url_root': config.get('ckan.cache_url_root')
        })
        api_url = urlparse.urljoin(config['ckan.site_url'], 'api/action')

        if cmd == 'update':
            if len(self.args) > 1:
                data = json.dumps({'id': unicode(self.args[1])})
                response = requests.post(api_url + '/package_show', data)
                packages =  [json.loads(response.content).get('result')]
            else:
                response = requests.post(api_url + '/current_package_list_with_resources', "{}")
                packages = json.loads(response.content).get('result')

            logger.info("Number of datasets to archive: %d" % len(packages))

            for package in packages:
                logger.info("Archiving dataset: %s (%d resources)" % (package.get('name'), len(package.get('resources', []))))
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
            logger.error('Command %s not recognized' % (cmd,))

