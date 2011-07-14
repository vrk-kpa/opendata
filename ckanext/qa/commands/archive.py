import sys
import os
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.model import Package, Session, repo
from ckanext.qa.lib.archive import archive_resource
from ckanext.qa.lib.log import log, set_config

# Use this specific author so that these revisions can be filtered out of
# normal RSS feeds that cover significant package changes. See DGU#982.
MAINTENANCE_AUTHOR = u'okfn_maintenance'

class Archive(CkanCommand):
    """
    Download and save copies of all package resources.

    If we already have a copy of a resource (tested by checking the hash value),
    then it is not saved again.
    The result of each download attempt is saved to a webstore database, so the
    information can be used later for QA analysis.

    Usage:

        paster archive update [{package-id}]
           - Archive all resources or just those belonging to a specific package 
             if a package id is provided

        paster archive clean        
            - Remove all archived resources

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster archive --config=../ckan/development.ini
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 
    pkg_names = []

    existing_dests = [o.dest for o in CkanCommand.parser.option_list]
    if not 'start' in existing_dests:
        CkanCommand.parser.add_option('-s', '--start',
            action='store',
            dest='start',
            default=False,
            help="""Start the process from the specified package.
                    (Ignored if a package id is provided as an argument)"""
        )
    if not 'limit' in existing_dests:
        CkanCommand.parser.add_option('-l', '--limit',
            action='store',
            dest='limit',
            default=False,
            help="""Limit the process to a number of packages.
                    (Ignored if a package id is provided as an argument)"""
        )
    if not 'force' in existing_dests:
        CkanCommand.parser.add_option('-o', '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force the score update even if it already exists."
        )

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print Archive.__doc__
            return

        self._load_config()
        set_config(self.options.config)
        self.archive_folder = os.path.join(config['ckan.qa_archive'], 'downloads')
        cmd = self.args[0]

        if cmd == 'update':
            self.update(unicode(self.args[1]) if len(self.args) > 1 else None)
        elif cmd == 'clean':
            self.clean()
        else:
            log.error('Command %s not recognized' % (cmd,))

    def clean(self):
        """
        Remove all archived resources.
        """
        log.error("clean not implemented yet")

    def update(self, package_id=None):
        """
        Archive all resources, or just those belonging to 
        package_id if provided.
        """
        # check that archive folder exists
        if not os.path.exists(self.archive_folder):
            log.info("Creating archive folder: %s" % self.archive_folder)
            os.mkdir(self.archive_folder)
        db_file = os.path.join(self.archive_folder, 'archive.db')

        if package_id:
            package = Package.get(package_id)
            if package:
                packages = [package]
            else:
                log.info("Error: Package not found: %s" % package_id)
        else:
            start = self.options.start
            limit = int(self.options.limit or 0)
            if start:
                ids = Session.query(Package.id).order_by(Package.id).all()
                index = [i for i,v in enumerate(ids) if v[0] == start]
                if not index:
                    log.error('Error: Package not found: %s' % start)
                    sys.exit()
                if limit is not False:
                    ids = ids[index[0]:index[0] + limit]
                else:
                    ids = ids[index[0]:]
                packages = [Session.query(Package).filter(Package.id == id[0]).first() for id in ids]
            else:
                if limit:
                    packages = Session.query(Package).limit(limit).all()
                else:
                    packages = Session.query(Package).all()

        log.info("Total packages to update: %d" % len(packages))
        if not packages:
            return

        revision = repo.new_revision()
        revision.author = MAINTENANCE_AUTHOR
        revision.message = u'Update resource hash values'

        for package in packages:
            log.info("Checking package: %s" % package.name)
            for resource in package.resources:
                log.info("Attempting to archive resource: %s" % resource.url)
                archive_resource(self.archive_folder, db_file, resource, package.name)

        repo.commit()
        repo.commit_and_remove()
