import logging
import os
import sys
import time
import re
import shutil
import itertools

from pylons import config

from ckan.lib.cli import CkanCommand

REQUESTS_HEADER = {'content-type': 'application/json'}


class Archiver(CkanCommand):
    '''
    Download and save copies of all package resources.

    The result of each download attempt is saved to the CKAN task_status table,
    so the information can be used later for QA analysis.

    Usage:

        paster archiver init
           - Creates the database table archiver needs to run

        paster archiver update [{package-name/id}|{group-name/id}]
           - Archive all resources or just those belonging to a specific
             package or group, if specified

        paster archiver clean-status
           - Cleans the TaskStatus records that contain the status of each
             archived resource, whether it was successful or not, with errors.
             It does not change the cache_url etc. in the Resource

        paster archiver clean-cached-resources
           - Removes all cache_urls and other references to resource files on
             disk.

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
        elif cmd == 'init':
            import ckan.model as model
            from ckanext.archiver.model import init_tables
            init_tables(model.meta.engine)
            self.log.info('Archiver tables are initialized')
        elif cmd == 'migrate-archive-dirs':
            self.migrate_archive_dirs()
        else:
            self.log.error('Command %s not recognized' % (cmd,))

    def update(self):
        from ckan import model
        from ckanext.archiver import lib
        packages = []
        resources = []
        if len(self.args) > 1:
            for arg in self.args[1:]:
                # try arg as a group id/name
                group = model.Group.get(arg)
                if group:
                    if group.is_organization:
                        packages.extend(
                            model.Session.query(model.Package)
                                 .filter_by(owner_org=group.id))
                    else:
                        packages.extend(group.packages(with_private=True))
                    if not self.options.queue:
                        self.options.queue = 'bulk'
                    continue
                # try arg as a package id/name
                pkg = model.Package.get(arg)
                if pkg:
                    packages.append(pkg)
                    if not self.options.queue:
                        self.options.queue = 'priority'
                    continue
                # try arg as a resource id
                res = model.Resource.get(arg)
                if res:
                    resources.append(res)
                    if not self.options.queue:
                        self.options.queue = 'priority'
                    continue
                else:
                    self.log.error('Could not recognize as a group, package '
                                   'or resource: %r', arg)
                    sys.exit(1)
        else:
            # all packages
            pkgs = model.Session.query(model.Package)\
                        .filter_by(state='active')\
                        .order_by('name').all()
            packages.extend(pkgs)
            if not self.options.queue:
                self.options.queue = 'bulk'

        if packages:
            self.log.info('Datasets to archive: %d', len(packages))
        if resources:
            self.log.info('Resources to archive: %d', len(resources))
        if not (packages or resources):
            self.log.error('No datasets or resources to process')
            sys.exit(1)

        self.log.info('Queue: %s', self.options.queue)
        for package in packages:
            if hasattr(model, 'ResourceGroup'):
                # earlier CKANs had ResourceGroup
                pkg_resources = \
                    [res for res in
                        itertools.chain.from_iterable(
                            (rg.resources_all
                             for rg in package.resource_groups_all)
                        )
                     if res.state == 'active']
            else:
                pkg_resources = \
                    [res for res in package.resources_all
                     if res.state == 'active']
            self.log.info('Queuing dataset %s (%s resources)',
                          package.name, len(pkg_resources))
            lib.create_archiver_package_task(package, self.options.queue)
            time.sleep(0.1)  # to try to avoid Redis getting overloaded

        for resource in resources:
            package = resource.resource_group.package
            self.log.info('Queuing resource %s/%s', package.name, resource.id)
            lib.create_archiver_resource_task(resource, self.options.queue)
            time.sleep(0.05)  # to try to avoid Redis getting overloaded

        self.log.info('Completed queueing')

    def view(self, package_ref=None):
        from ckan import model
        from ckanext.archiver.model import Archival

        r_q = model.Session.query(model.Resource).filter_by(state='active')
        print 'Resources: %i total' % r_q.count()
        a_q = model.Session.query(Archival)
        print 'Archived resources: %i total' % a_q.count()
        num_with_cache_url = a_q.filter(Archival.cache_url!='').count()
        print '                    %i with cache_url' % num_with_cache_url
        last_updated_res = a_q.order_by(Archival.updated.desc()).first()
        print 'Latest archival: %s' % (last_updated_res.updated.strftime('%Y-%m-%d %H:%M') if last_updated_res else '(no)')

        if package_ref:
            pkg = model.Package.get(package_ref)
            print 'Package %s %s' % (pkg.name, pkg.id)
            for res in pkg.resources:
                print 'Resource %s' % res.id
                for archival in a_q.filter_by(resource_id=res.id):
                    print '* %r' % archival

    def clean_status(self):
        from ckan import model
        from ckanext.archiver.model import Archival

        print 'Before:'
        self.view()

        q = model.Session.query(Archival)
        q.delete()
        model.Session.commit()

        print 'After:'
        self.view()

    def clean_cached_resources(self):
        from ckan import model
        from ckanext.archiver.model import Archival

        print 'Before:'
        self.view()

        q = model.Session.query(Archival).filter(Archival.cache_url != '')
        archivals = q.all()
        num_archivals = len(archivals)
        progress = 0
        for archival in archivals:
            archival.cache_url = None
            archival.cache_filepath = None
            archival.size = None
            archival.mimetype = None
            archival.hash = None
            progress += 1
            if progress % 1000 == 0:
                print 'Done %i/%i' % (progress, num_archivals)
                model.Session.commit()
        model.Session.commit()
        model.Session.remove()

        print 'After:'
        self.view()

    def report(self, output_file, delete=False):
        """
        Generates a report containing orphans (either files or resources)
        """
        import csv
        from ckan import model

        archive_root = config.get('ckanext-archiver.archive_dir')
        if not archive_root:
            self.log.error("Could not find archiver root")
            return

        # We'll use this to match the UUID part of the path
        uuid_re = re.compile(".*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).*")

        not_cached_active = 0
        not_cached_deleted = 0
        file_not_found_active = 0
        file_not_found_deleted = 0
        perm_error = 0
        file_no_resource = 0

        with open(output_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Resource ID", "Filepath", "Problem"])
            resources = {}
            for resource in model.Session.query(model.Resource).all():
                resources[resource.id] = True

                # Check the resource's cached_filepath
                fp = resource.extras.get('cache_filepath')
                if fp is None:
                    if resource.state == 'active':
                        not_cached_active += 1
                    else:
                        not_cached_deleted += 1
                    writer.writerow([resource.id, str(resource.extras), "Resource not cached: {0}".format(resource.state)])
                    continue

                # Check that the cached file is there and readable
                if not os.path.exists(fp):
                    if resource.state == 'active':
                        file_not_found_active += 1
                    else:
                        file_not_found_deleted += 1

                    writer.writerow([resource.id, fp.encode('utf-8'), "File not found: {0}".format(resource.state)])
                    continue

                try:
                    os.stat(fp)
                except OSError:
                    perm_error += 1
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
                        file_no_resource += 1

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

        print "General info:"
        print "  Permission error reading file: {0}".format(perm_error)
        print "  file on disk but no resource: {0}".format(file_no_resource)
        print "  Total resources: {0}".format(model.Session.query(model.Resource).count())
        print "Active resource info:"
        print "  No cache_filepath: {0}".format(not_cached_active)
        print "  cache_filepath not on disk: {0}".format(file_not_found_active)
        print "Deleted resource info:"
        print "  No cache_filepath: {0}".format(not_cached_deleted)
        print "  cache_filepath not on disk: {0}".format(file_not_found_deleted)

    def migrate_archive_dirs(self):
        from ckan import model
        from ckan.logic import get_action

        site_user = get_action('get_site_user')(
            {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )

        site_url_base = config['ckanext-archiver.cache_url_root'].rstrip('/')
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
