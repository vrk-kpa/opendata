import pkg_resources
import logging
import os
import sys
from datetime import datetime
import json
import urlparse
import re
import shutil

import requests
from pylons import config
from pylons.test import pylonsapp
from paste.deploy import loadapp
import paste.fixture
import paste

from ckan.lib.cli import CkanCommand

REQUESTS_HEADER = {'content-type': 'application/json'}

class Archiver(CkanCommand):
    '''
    Download and save copies of all package resources.

    The result of each download attempt is saved to the CKAN task_status table, so the
    information can be used later for QA analysis.

    Usage:

        paster archiver update [{package-name/id}|{group-name/id}]
           - Archive all resources or just those belonging to a specific
             package or group, if specified

        paster archiver clean-status
           - Cleans the TaskStatus records that contain the status of each
             archived resource, whether it was successful or not, with errors.
             It does not change the cache_url etc. in the Resource

        paster archiver view [{dataset name/id}]
           - Views info archival info, in general and if you specify one, about
             a particular dataset\'s resources.

        paster archiver migrate-archive-dirs
           - Migrate the layout of the archived resource directories.
             Previous versions of ckanext-archiver stored resources on disk
             at: {resource-id}/filename.csv and this version puts them at:
             {2-chars-of-resource-id}/{resource-id}/filename.csv
             Running this moves them to the new locations and updates the
             cache_url on each resource to reflect the new location.
    '''
    # TODO
    #    paster archiver clean-files
    #       - Remove all archived resources
    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2

    def __init__(self, name):
        super(Archiver, self).__init__(name)
        self.parser.add_option('-q', '--queue',
                               action='store',
                               dest='queue',
                               help='Send to a particular queue')

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.usage
            sys.exit(1)

        cmd = self.args[0]
        self._load_config()

        # Initialise logger after the config is loaded, so it is not disabled.
        self.log = logging.getLogger(__name__)

        if cmd == 'update':
            self.update()
        elif cmd == 'clean-status':
            self.clean_status()
        elif cmd == 'view':
            if len(self.args) == 2:
                self.view(self.args[1])
            else:
                self.view()
        elif cmd == 'migrate-archive-dirs':
            self.migrate_archive_dirs()
        else:
            self.log.error('Command %s not recognized' % (cmd,))

    def update(self):
        from ckan.logic import get_action
        from ckan import model
        from ckan.model.types import make_uuid
        import tasks
        user = get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})
        context = json.dumps({
            'site_url': config.get('ckan.site_url_internally') or config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'site_user_apikey': user.get('apikey'),
            'username': user.get('name'),
            'cache_url_root': config.get('ckan.cache_url_root')
        })
        api_url = urlparse.urljoin(config.get('ckan.site_url_internally') or config['ckan.site_url'], 'api/action')
        if len(self.args) > 1:
            # try arg as a group name
            url = api_url + '/member_list'
            self.log.info('Requesting list of datasets from %r', url)
            data = {'id': self.args[1],
                    'object_type': 'package',
                    'capacity': 'public'}
            response = requests.post(url, data=json.dumps(data), headers=REQUESTS_HEADER)
            self.log.info('List of datasets (status %s): %r...', response.status_code, response.text[:100])
            if response.status_code == 200:
                package_tuples = json.loads(response.text).get('result')
                package_names = [pt[0] for pt in package_tuples]
                if not self.options.queue:
                    self.options.queue = 'bulk'
            else:
                # must be a package id
                package_names = [self.args[1]]
                if not self.options.queue:
                    self.options.queue = 'priority'
        else:
            url = api_url + '/package_list'
            self.log.info('Requesting list of datasets from %r', url)
            response = requests.post(url, data="{}", headers=REQUESTS_HEADER)
            self.log.info('List of datasets (status %s): %r...', response.status_code, response.text[:100])
            package_names = json.loads(response.text).get('result')
            if not self.options.queue:
                self.options.queue = 'bulk'

        self.log.info("Number of datasets to archive: %d" % len(package_names))

        for package_name in package_names:
            self.log.info('Getting dataset metadata: %s', package_name)

            # Get the dataset's resource urls
            data = json.dumps({'id': unicode(package_name)})
            response = requests.post(api_url + '/package_show', data=data,
                                     headers=REQUESTS_HEADER)
            if response.status_code == 403:
                self.log.warn('Dataset %s gave 403 - ignoring' % package_name)
                continue
            assert response.status_code == 200, response.status_code
            package = json.loads(response.text).get('result')

            self.log.info('Archival of dataset resource data added to celery queue "%s": %s (%d resources)' % (self.options.queue, package.get('name'), len(package.get('resources', []))))
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
                tasks.update.apply_async(args=[context, data], task_id=task_id, queue=self.options.queue)

    def view(self, package_ref=None):
        from ckan import model

        r_q = model.Session.query(model.Resource)
        print 'Resources: %i total' % r_q.count()
        r_q = r_q.filter(model.Resource.cache_url!='')
        print '           %i with cache_url' % r_q.count()
        print '           %s latest update' % r_q.order_by(model.Resource.cache_last_updated.desc()).first().last_modified
        
        ts_q = model.Session.query(model.TaskStatus).filter_by(task_type='archiver')
        print 'Archive status records - %i TaskStatus rows' % ts_q.count()
        print '                  across %i Resources' % ts_q.distinct('entity_id').count()

        if package_ref:
            pkg = model.Package.get(package_ref)
            print 'Package %s %s' % (pkg.name, pkg.id)
            for res in pkg.resources:
                print 'Resource %s' % res.id
                for row in ts_q.filter_by(entity_id=res.id):
                    print '* TS %s = %r error=%r' % (row.key, row.value, row.error) 
                for row in r_q.filter_by(id=res.id):
                    print '* cache_url=%r size=%s mimetype=%s cache_last_updated=%r' % \
                          (row.cache_url, row.size, row.mimetype, row.cache_last_updated)

    def clean_status(self):
        from ckan import model

        print 'Before:'
        self.view()

        q = model.Session.query(model.TaskStatus).filter_by(task_type='qa')
        q.delete()
        model.Session.commit()

        print 'After:'
        self.view()        

    def migrate_archive_dirs(self):
        from ckan import model
        from ckanext.archiver.tasks import get_status as ArchiverError
        from ckanext.archiver.lib import get_cached_resource_filepath

        site_url_base = config['ckan.cache_url_root'].rstrip('/')
        old_dir_regex = re.compile(r'(.*)/([a-f0-9\-]+)/([^/]*)$')
        new_dir_regex = re.compile(r'(.*)/[a-f0-9]{2}/[a-f0-9\-]{36}/[^/]*$')
        for resource in model.Session.query(model.Resource).\
            filter(model.Resource.state != model.State.DELETED):
            if not resource.cache_url or resource.cache_url == 'None':
                continue
            if new_dir_regex.match(resource.cache_url):
                print 'Resource with new url already: %s' % resource.cache_url
                continue
            match = old_dir_regex.match(resource.cache_url)
            if not match:
                print 'ERROR Could not match url: %s' % resource.cache_url
                continue
            url_base, res_id, filename = match.groups()

            if url_base != site_url_base:
                print 'ERROR Base URL is incorrect: %r != %r' % (url_base, site_url_base)
                continue

            # move the file
            filepath_base = config['ckanext-archiver.archive_dir']
            old_path = os.path.join(filepath_base, resource.id)
            new_dir = os.path.join(filepath_base, resource.id[:2])
            new_path = os.path.join(filepath_base, resource.id[:2], resource.id)
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            if os.path.exists(new_path) and not os.path.exists(old_path):
                print 'File already moved: %s' % new_path
            else:
                print 'File: "%s" -> "%s"' % (old_path, new_path)
                shutil.move(old_path, new_path)

            # change the cache_url
            new_cache_url = '/'.join((url_base, res_id[:2], res_id, filename))
            rev = model.repo.new_revision()
            rev.message = 'Migrating cache urls to new location'
            print 'Cache_url: "%s" -> "%s"' % (resource.cache_url, new_cache_url)
            resource.cache_url = new_cache_url
            model.repo.commit_and_remove()
