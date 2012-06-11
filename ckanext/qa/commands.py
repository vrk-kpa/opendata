import datetime
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


class QACommand(CkanCommand):
    """
    QA analysis of CKAN resources

    Usage::

        paster qa [options] update [dataset name/id]
           - QA analysis on all resources in a given dataset, or on all
           datasets if no dataset given

        paster qa clean
            - Remove all package score information

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster qa update --config=<path to CKAN config file>
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 0

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print QACommand.__doc__
            return

        cmd = self.args[0]
        self._load_config()

        # import tasks after load config so CKAN_CONFIG evironment variable
        # can be set
        import tasks

        user = get_action('get_site_user')(
            {'model': model, 'ignore_auth': True}, {}
        )
        context = json.dumps({
            'site_url': config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'username': user.get('name'),
        })

        if cmd == 'update':
            for package in self._package_list():
                logger.info("Updating QA on dataset: %s (%d resources)" %
                            (package.get('name'), len(package.get('resources', []))))

                for resource in package.get('resources', []):
                    data = json.dumps(resource)
                    task_id = make_uuid()
                    task_status = {
                        'entity_id': resource['id'],
                        'entity_type': u'resource',
                        'task_type': u'qa',
                        'key': u'celery_task_id',
                        'value': task_id,
                        'error': u'',
                        'last_updated': datetime.datetime.now().isoformat()
                    }
                    task_context = {
                        'model': model,
                        'user': user.get('name')
                    }

                    get_action('task_status_update')(task_context, task_status)
                    tasks.update.apply_async(args=[context, data], task_id=task_id)

        elif cmd == 'clean':
            logger.error('Command "%s" not implemented' % (cmd,))

        else:
            logger.error('Command "%s" not recognized' % (cmd,))

    def _package_list(self):
        """
        Generate the package dicts as declared in self.args.

        Make API calls for the packages declared in self.args, and generate
        the package dicts.

        If no packages are declared in self.args, then retrieve all the
        packages from the catalogue.
        """
        api_url = urlparse.urljoin(config['ckan.site_url'], 'api/action')
        if len(self.args) > 1:
            for id in self.args[1:]:
                data = json.dumps({'id': unicode(id)})
                response = requests.post(api_url + '/package_show', data)
                yield json.loads(response.content).get('result')
        else:
            page, limit = 1, 100
            response = requests.post(api_url + '/current_package_list_with_resources',
                                     json.dumps({'page': page, 'limit': limit}))
            chunk = json.loads(response.content).get('result')
            while(chunk):
                page += 1
                for p in chunk:
                    yield p
                response = requests.post(api_url + '/current_package_list_with_resources',
                                         json.dumps({'page': page, 'limit': limit}))
                chunk = json.loads(response.content).get('result')
