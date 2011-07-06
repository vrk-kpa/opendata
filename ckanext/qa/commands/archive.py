import sys
import os
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.model import Session, Package
from ckanext.qa.lib.sqlite import resource_to_sqlite

# Use this specific author so that these revisions can be filtered out of
# normal RSS feeds that cover significant package changes. See DGU#982.
MAINTENANCE_AUTHOR = u'okfn_maintenance'

class Archive(CkanCommand):
    """
    Create SQLite and JSONP representations of all package resources that
    are in csv format.

    Usage::

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

    def update(self, package_id=None):
        """
        Archive all resources, or just those belonging to 
        package_id if provided.
        """
        if not os.path.exists(self.archive_folder):
            os.mkdir(self.archive_folder)

        # print "Total packages to update:", len(packages)
        # only archive specific packages for now
        if not package_id:
            return

        package = Package.get(package_id)
        print "Checking package:", package.name, "(" + str(package.id) + ")"

        # look at each resource in the package
        for resource in package.resources:
            # check the resource hash
            if not resource.hash:
                print "No hash found for", resource.url, "- skipping"
                break
            # save the resource if we don't already have a copy of it
            db_file = resource.hash + ".sqlite"
            if not db_file in os.listdir(self.archive_folder):
                print "No archived copy of", resource.url, "found - archiving"
                # find the copy of the resource that should have already been downloaded
                # by the package-score command
                resource_file = os.path.join(self.downloads_folder, package.name)
                resource_file = os.path.join(resource_file, resource.hash + ".csv")
                db_file = os.path.join(self.archive_folder, db_file)
                # convert this resource into an sqlite database
                resource_to_sqlite(resource.format.lower(), resource_file, db_file)
