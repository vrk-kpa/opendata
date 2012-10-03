import datetime
import json
import requests
import urlparse
import logging
import sys
import logging

from pylons import config

import ckan.plugins as p
from ckan.lib.cli import CkanCommand

REQUESTS_HEADER = {'content-type': 'application/json'}

class CkanApiError(Exception):
    pass


class QACommand(p.toolkit.CkanCommand):
    """
    QA analysis of CKAN resources

    Usage::

        paster qa [options] update [dataset/group name/id]
           - QA analysis on all resources in a given dataset, or on all
           datasets if no dataset given

        paster qa sniff {filepath}
           - Opens the file and determines its type by the contents

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster qa update --config=<path to CKAN config file>
    """
    # TODO
    #    paster qa clean
    #        - Remove all package score information
    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0

    def __init__(self, name):
        super(QACommand, self).__init__(name)
        self.parser.add_option('-q', '--queue',
                               action='store',
                               dest='queue',
                               help='Send to a particular queue')

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

        from ckan.logic import get_action
        from ckan import model

        user = p.toolkit.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True}, {}
        )
        context = json.dumps({
            'site_url': config.get('ckan.site_url_internally') or config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'username': user.get('name'),
        })

        if cmd == 'update':
            self.update(user, context)
        elif cmd == 'sniff':
            self.sniff()
        elif cmd == 'clean':
            self.log.error('Command "%s" not implemented' % (cmd,))
        else:
            self.log.error('Command "%s" not recognized' % (cmd,))

    def update(self, user, context):
        from ckan.model.types import make_uuid
        from ckan.logic import get_action
        from ckan import model
        # import tasks after load config so CKAN_CONFIG evironment variable
        # can be set
        import tasks

        if not self.options.queue:
            self.options.queue = 'priority' if len(self.args) > 1 \
                                 else 'bulk'

        for package in self._package_list():
            self.log.info('QA on dataset being added to Celery queue "%s": %s (%d resources)' % \
                        (self.options.queue, package.get('name'),
                         len(package.get('resources', []))))

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
                tasks.update.apply_async(args=[context, data],
                                         task_id=task_id,
                                         queue=self.options.queue)


    def _package_list(self):
        """
        Generate the package dicts as declared in self.args.

        Make API calls for the packages declared in self.args, and generate
        the package dicts.

        If no packages are declared in self.args, then retrieve all the
        packages from the catalogue.
        """
        api_url = urlparse.urljoin(config.get('ckan.site_url_internally') or config['ckan.site_url'], 'api/action')
        if len(self.args) > 1:
            for id in self.args[1:]:
                # try arg as a group name
                url = api_url + '/member_list'
                self.log.info('Requesting list of datasets from %r', url)
                data = {'id': id,
                        'object_type': 'package',
                        'capacity': 'public'}
                response = requests.post(url, data=json.dumps(data), headers=REQUESTS_HEADER)
                if response.status_code == 200:
                    package_tuples = json.loads(response.text).get('result')
                    package_names = [pt[0] for pt in package_tuples]
                    if not self.options.queue:
                        self.options.queue = 'bulk'
                else:
                    # must be a package id
                    package_names = [id]
                    if not self.options.queue:
                        self.options.queue = 'priority'
                for package_name in package_names:
                    data = json.dumps({'id': unicode(package_name)})
                    url = api_url + '/package_show'
                    response = requests.post(url, data, headers=REQUESTS_HEADER)
                    if not response.ok:
                        err = ('Failed to get package %s from url %r: %s' %
                               (id, url, response.error))
                        self.log.error(err)
                        raise CkanApiError(err)
                    yield json.loads(response.content).get('result')
        else:
            if not self.options.queue:
                self.options.queue = 'bulk'
            page, limit = 1, 100
            url = api_url + '/current_package_list_with_resources'
            response = requests.post(url,
                                     json.dumps({'page': page, 'limit': limit}),
                                     headers=REQUESTS_HEADER)
            if not response.ok:
                err = ('Failed to get package list with resources from url %r: %s' %
                       (url, response.error))
                self.log.error(err)
                raise CkanApiError(err)
            chunk = json.loads(response.content).get('result')
            while(chunk):
                page += 1
                for p in chunk:
                    yield p
                url = api_url + '/current_package_list_with_resources'
                response = requests.post(url,
                                         json.dumps({'page': page, 'limit': limit}),
                                         headers=REQUESTS_HEADER)
                if not response.ok:
                    err = ('Failed to get package list with resources from url %r: %s' %
                           (url, response.error))
                    self.log.error(err)
                    raise CkanApiError(err)
                chunk = json.loads(response.content).get('result')

    def sniff(self):
        from ckanext.qa.sniff_format import sniff_file_format
        
        if len(self.args) < 2:
            print 'Not enough arguments', self.args
            sys.exit(1)
        for filepath in self.args[1:]:
            format_ = sniff_file_format(filepath, logging.getLogger('ckanext.qa.sniffer'))
            if format_:
                print 'Detected as: %s' % format_['display_name']
            else:
                print 'ERROR: Could not recognise format of: %s' % filepath
