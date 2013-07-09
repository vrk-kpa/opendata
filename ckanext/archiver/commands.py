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

        paster archiver clean-cached-resources
           - Removes all cache_urls and other references to resource files on disk.

        paster archiver view [{dataset name/id}]
           - Views info archival info, in general and if you specify one, about
             a particular dataset\'s resources.

        paster archiver report [outputfile]
           - Generates a report on orphans, either resources where the path
             does not exist, or files on disk that don't have a corresponding
             orphan. The outputfile parameter is the name of the CSV output
             from running the report

        paster archiver delete-orphans [outputfile]
           - Deletes orphans that are files on disk with no corresponding
             resource. This uses the report command and will write out a
             report to [outputfile]

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
        elif cmd == 'clean-cached-resources':
            self.clean_cached_resources()
        elif cmd == 'view':
            if len(self.args) == 2:
                self.view(self.args[1])
            else:
                self.view()
        elif cmd == 'report':
            if len(self.args) != 2:
                self.log.error('Command requires a parameter, the name of the output')
                return
            self.report(self.args[1], delete=False)
        elif cmd == 'delete-orphans':
            if len(self.args) != 2:
                self.log.error('Command requires a parameter, the name of the output')
                return
            self.report(self.args[1], delete=True)
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

        for package_name in sorted(package_names):
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
                tasks.update.apply_async(args=[context, data], task_id=task_id, queue=self.options.queue)

    def view(self, package_ref=None):
        from ckan import model

        r_q = model.Session.query(model.Resource)
        print 'Resources: %i total' % r_q.count()
        r_q = r_q.filter(model.Resource.cache_url!='')
        print '           %i with cache_url' % r_q.count()
        last_updated_res = r_q.order_by(model.Resource.cache_last_updated.desc()).first()
        print '           %s latest update' % (last_updated_res.last_modified if last_updated_res else '(no)')
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

    def clean_cached_resources(self):
        from ckan import model

        print 'Before:'
        self.view()

        def new_revision():
            rev = model.repo.new_revision()
            rev.message = 'Refresh cached resources'

        q = model.Session.query(model.Resource).filter(model.Resource.cache_url!='')
        resources = q.all()
        num_resources = len(resources)
        progress = 0
        rev = new_revision()
        for res in resources:
            res.cache_url = ''
            res.cache_last_updated = None
            if 'cache_filepath' in res.extras:
                del res.extras['cache_filepath']
            progress += 1
            if progress % 1000 == 0:
                print 'Done %i/%i' % (progress, num_resources)
                model.Session.commit()
                rev = new_revision()
        model.Session.commit()
        model.Session.remove()

        print 'After:'
        self.view()

    def report(self, output_file, delete=False):
        """
        Generates a report containing orphans (either files or resources)
        """
        import re
        import csv
        from ckan import model

        archive_root = config.get('ckanext-archiver.archive_dir')
        if not archive_root:
            log.error("Could not find archiver root")
            return

        # We'll use this to match the UUID part of the path
        uuid_re = re.compile(".*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).*")


        with open(output_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Resource ID", "Filepath", "Problem"])
            resources = {}
            for resource in model.Session.query(model.Resource).all():
                resources[resource.id] = True

                # Check the resource's cached_filepath
                fp = resource.extras.get('cache_filepath')
                if fp is None:
                    if not delete:
                        writer.writerow([resource.id, str(resource.extras), "Resource not cached"])
                    continue

                # Check that the cached file is there and readable
                if not os.path.exists(fp):
                    if not delete:
                        writer.writerow([resource.id, fp.encode('utf-8'), "File not found"])
                    continue

                try:
                    s = os.stat(fp)
                except OSError:
                    if not delete:
                        writer.writerow([resource.id, fp.encode('utf-8'), "File not readable"])
                    continue

            # Iterate over the archive root and check each file by matching the
            # resource_id part of the path to the resources dict
            for root, _, files in os.walk(archive_root):
                for filename in files:
                    archived_path = os.path.join(root, filename)
                    m = uuid_re.match(archived_path)
                    if not m:
                        writer.writerow([resource.id, archived_path, "Malformed path (no UUID)"])
                        continue

                    if not resources.get(m.groups(0)[0].strip(), False):
                        if delete:
                            try:
                                os.unlink(archived_path)
                                self.log.info("Unlinked {0}".format(archived_path))
                                os.rmdir(root)
                                self.log.info("Unlinked {0}".format(root))
                                writer.writerow([m.groups(0)[0], archived_path, "Resource not found, file deleted"])
                            except Exception, e:
                                self.log.error("Failed to unlink {0}: {1}".format(archived_path,e))
                        else:
                            writer.writerow([m.groups(0)[0], archived_path, "Resource not found"])

                        continue




    def migrate_archive_dirs(self):
        from ckan import model
        from ckanext.archiver.tasks import get_status as ArchiverError
        from ckan.logic import get_action

        site_user = get_action('get_site_user')(
            {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )

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
            # check the package isn't deleted
            # Need to refresh the resource's session
            resource = model.Session.query(model.Resource).get(resource.id)
            if resource.resource_group and resource.resource_group.package:
                if resource.resource_group.package.state == model.State.DELETED:
                    print 'Package is deleted'
                    continue

            if url_base != site_url_base:
                print 'ERROR Base URL is incorrect: %r != %r' % (url_base, site_url_base)
                continue

            # move the file
            filepath_base = config['ckanext-archiver.archive_dir']
            old_path = os.path.join(filepath_base, resource.id)
            new_dir = os.path.join(filepath_base, resource.id[:2])
            new_path = os.path.join(filepath_base, resource.id[:2], resource.id)
            new_filepath = os.path.join(new_path, filename)
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            if os.path.exists(new_path) and not os.path.exists(old_path):
                print 'File already moved: %s' % new_path
            else:
                print 'File: "%s" -> "%s"' % (old_path, new_path)
                try:
                    shutil.move(old_path, new_path)
                except IOError, e:
                    print 'ERROR moving resource: %s' % e
                    continue

            # change the cache_url and cache_filepath
            new_cache_url = '/'.join((url_base, res_id[:2], res_id, filename))
            print 'cache_filepath: "%s" -> "%s"' % (resource.extras.get('cache_filepath'), new_filepath)
            print 'cache_url: "%s" -> "%s"' % (resource.cache_url, new_cache_url)
            context = {'model': model, 'user': site_user['name'], 'ignore_auth': True, 'session': model.Session}
            data_dict = {'id': resource.id}
            res_dict = get_action('resource_show')(context, data_dict)
            res_dict['cache_filepath'] = new_filepath
            res_dict['cache_url'] = new_cache_url
            data_dict = res_dict
            result = get_action('resource_update')(context, data_dict)
            if result.get('id') == res_id:
                print 'Successfully updated resource'
            else:
                print 'ERROR updating resource: %r' % result
