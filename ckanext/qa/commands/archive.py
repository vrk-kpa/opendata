import sys
import os
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.model import Package, Session

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

    CkanCommand.parser.add_option('-s', '--start',
        action='store',
        dest='start',
        default=False,
        help="""Start the process from the specified package.
                (Ignored if a package id is provided as an argument)"""
    )
    CkanCommand.parser.add_option('-l', '--limit',
        action='store',
        dest='limit',
        default=False,
        help="""Limit the process to a number of packages.
                (Ignored if a package id is provided as an argument)"""
    )
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
        self.downloads_folder = config['ckan.qa_downloads'] 
        self.archive_folder = config['ckan.qa_archive']
        cmd = self.args[0]

        if cmd == 'update':
            self.update(unicode(self.args[1]) if len(self.args) > 1 else None)
        elif cmd == 'clean':
            self.clean()
        else:
            sys.stderr.write('Command %s not recognized\n' % (cmd,))

    def clean(self):
        """
        Remove all archived resources.
        """
        print "clean not implemented yet"

    def _archive_package_resources(self, package):
        print package

    def update(self, package_id=None):
        """
        Archive all resources, or just those belonging to 
        package_id if provided.
        """
        # check that downloads folder exists
        if not os.path.exists(self.downloads_folder):
            print "Creating downloads folder:", self.downloads_folder
            os.mkdir(self.downloads_folder)

        if package_id:
            package = Package.get(package_id)
            if package:
                packages = [package]
            else:
                print "Error: Package not found:", package_id
        else:
            start = self.options.start
            limit = int(self.options.limit or 0)
            if start:
                ids = Session.query(Package.id).order_by(Package.id).all()
                index = [i for i,v in enumerate(ids) if v[0] == start]
                if not index:
                    sys.stderr.write('Error: Package not found: %s \n' % start)
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

        print "Total packages to update:", len(packages)
        for package in packages:
            self._archive_package_resources(package)
