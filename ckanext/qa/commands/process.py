import sys
import os
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.model import Package
from ckanext.qa.lib.db import resource_to_db

# This is the user name used to access the webstore database
WEBSTORE_USER = 'okfn'

class Process(CkanCommand):
    """
    Process all archived resources.

    Creates a SQLite database for each resource if not already present
    (determined by checking the hash value). 
    This is done using the webstore database module, so all resource
    databases can be served using the webstore API.

    Usage::

        paster process update [{package-id}]
           - Process all resources or just those belonging to a specific package 
             if a package id is provided

        paster process clean        
            - Remove all data created by the update command

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster process --config=../ckan/development.ini
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print Process.__doc__
            return

        self._load_config()
        self.archive_folder = os.path.join(config['ckan.qa_archive'], 'downloads')
        self.webstore_folder = os.path.join(config['ckan.qa_archive'], WEBSTORE_USER)
        cmd = self.args[0]

        if cmd == 'update':
            self.update(unicode(self.args[1]) if len(self.args) > 1 else None)
        elif cmd == 'clean':
            self.clean()
        else:
            sys.stderr.write('Command %s not recognized\n' % (cmd,))

    def clean(self):
        """
        Remove all data created by the update command.
        """
        print "clean not implemented yet"

    def _update_package(self, package):
        """
        Process all resources belonging to package
        """
        print "Checking package:", package.name, "(" + str(package.id) + ")"
        # look at each resource in the package
        for resource in package.resources:
            # check the resource hash
            if not resource.hash:
                print "No hash found for", resource.url, "- skipping"
                continue
            # save the resource if we don't already have a copy of it
            db_file = resource.hash + ".db"
            if not db_file in os.listdir(self.webstore_folder):
                print "No archived copy of", resource.url, "found - archiving"
                # find the copy of the resource that should have already been archived
                resource_file = os.path.join(self.archive_folder, package.name)
                resource_file = os.path.join(resource_file, resource.hash + ".csv")
                db_file = os.path.join(self.webstore_folder, db_file)
                # convert this resource into an sqlite database
                try:
                    resource_to_db(resource.format.lower(), resource_file, db_file)
                except Exception as e:
                    print "Error: Could not process", resource.url
                    print e.message
            else:
                print "Local copy of", resource.url, "found - skipping"

    def update(self, package_id=None):
        """
        Process all resources, or just those belonging to 
        package_id if provided.
        """
        # check that archive and webstore folders exist
        if not os.path.exists(self.archive_folder):
            print "No archived resources available to process"
            return
        if not os.path.exists(self.webstore_folder):
            os.mkdir(self.webstore_folder)

        if package_id:
            package = Package.get(package_id)
            if package:
                packages = [package]
            else:
                print "Error: Package not found:", package_id
        else:
            # All resources that we can process should be stored
            # in a folder with the same name as their package in the
            # ckan.qa_archive folder. Get a list of package names by
            # these folders, then use the name to get the package object
            # from the database.
            files = os.listdir(self.archive_folder)
            package_names = [f for f in files if os.path.isdir(os.path.join(self.archive_folder, f))]
            package_names = [unicode(p) for p in package_names]
            packages = [Package.get(p) for p in package_names]

        print "Total packages to update:", len(packages)
        for package in packages:
            self._update_package(package)
