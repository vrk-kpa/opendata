import datetime
import json
import requests
import urlparse
import logging
from pylons import config

import ckan.plugins as p


REQUESTS_HEADER = {'content-type': 'application/json'}

class CkanApiError(Exception):
    pass


class QACommand(p.toolkit.CkanCommand):
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

        # Now we can import ckan and create logger, knowing that loggers
        # won't get disabled
        self.log = logging.getLogger('ckanext.qa')

        from ckan import model
        from ckan.model.types import make_uuid

        # import tasks after load config so CKAN_CONFIG evironment variable
        # can be set
        import tasks

        user = p.toolkit.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True}, {}
        )
        context = json.dumps({
            'site_url': config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'username': user.get('name'),
        })

        if cmd == 'update':
            for package in self._package_list():
                self.log.info("QA on dataset being added to Celery queue: %s (%d resources)" % 
                            (package.get('name'), len(package.get('resources', []))))

                for resource in package.get('resources', []):
                    resource['package'] = package['name']
                    pkg = model.Package.get(package['id'])
                    resource['is_open'] = pkg.isopen()
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

                    p.toolkit.get_action('task_status_update')(task_context, task_status)
                    tasks.update.apply_async(args=[context, data], task_id=task_id)

        elif cmd == 'clean':
            self.log.error('Command "%s" not implemented' % (cmd,))

        else:
            self.log.error('Command "%s" not recognized' % (cmd,))

    def make_post(self, url, data):
            headers = {'Content-type': 'application/json',
                       'Accept': 'text/plain'}
            return requests.post(url, data=json.dumps(data), headers=headers)

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
                data = {'id': unicode(id)}
                url = api_url + '/package_show'
                response = self.make_post(url, data)
                if not response.ok:
                    err = ('Failed to get package %s from url %r: %s' %
                           (id, url, response.reason))
                    self.log.error(err)
                    raise CkanApiError(err)
                yield json.loads(response.content).get('result')
        else:
            page, limit = 1, 100
            url = api_url + '/current_package_list_with_resources'
            response = self.make_post(url, {'page': page, 'limit': limit})
            if not response.ok:
                err = ('Failed to get package list with resources from url %r: %s' %
                       (url, response.reason))
                self.log.error(err)
                raise CkanApiError(err)
            chunk = json.loads(response.content).get('result')
            while(chunk):
                page += 1
                for p in chunk:
                    yield p
                url = api_url + '/current_package_list_with_resources'
                response = self.make_post(url, {'page': page, 'limit': limit})

                try:
                    response.raise_for_status()
                except requests.exceptions.RequestException, e:
                    err = ('Failed to get package list with resources from url %r: %s' %
                       (url, str(e)))
                    self.log.error(err)
                    raise CkanApiError(err)
                chunk = json.loads(response.content).get('result')
