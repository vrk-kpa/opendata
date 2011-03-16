import sys
from ckan.lib.cli import CkanCommand

from ckan.model import Session, Package, PackageExtra, repo
from ckanext.qa.lib.package_scorer import update_package_score
from ckanext.qa.lib.package_scorer import PKGEXTRA


class PackageScore(CkanCommand):
    '''Manage the ratings stored in the db

    Usage::

        paster package-scores [options] update [{package-id}]
           - Update all package scores or just one if a package id is provided

        paster package-scores clean        
            - Remove all package score information

    Available options::

        -s {package-id} Start the process from the specified package.
                        (Ignored if a package id is provided as an argument)

        -l {int}        Limit the process to a number of packages.
                        (Ignored if a package id is provided as an argument)

        -o              Force the score update even if it already exists.

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster package-scores update --config=../ckan/development.ini

    '''    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2 
    min_args = 0

    pkg_names = []
    tag_names = []
    group_names = set()
    user_names = []
    CkanCommand.parser.add_option('-s', '--start',
        action='store',
        dest='start',
        default=False,
        help="""
Start the process from the specified package.
        (Ignored if a package id is provided as an argument)
        """)
    CkanCommand.parser.add_option('-l', '--limit',
        action='store',
        dest='limit',
        default=False,
        help="""
Limit the process to a number of packages.
        (Ignored if a package id is provided as an argument)
        """)
    CkanCommand.parser.add_option('-o', '--force',
        action='store_true',
        dest='force',
        default=False,
        help="""
Force the score update even if it already exists.
        """)

    def command(self):
        self.verbose = 3

        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print PackageScore.__doc__
        else:
            self._load_config()
            cmd = self.args[0]
            if cmd == 'update':
                self.update()
            elif cmd == 'clean':
                self.clean()
            else:
                sys.stderr.write('Command %s not recognized\n' % (cmd,))

    def clean(self, user_ratings=True):

        revision = repo.new_revision()
        revision.author = u'cli script'
        revision.message = u'Update package scores from cli'

        for item in Session.query(PackageExtra).filter(PackageExtra.key.in_(PKGEXTRA)).all():
            item.purge()
        repo.commit_and_remove()

    def update(self, user_ratings=True):
        revision = repo.new_revision()
        revision.author = u'cli script'
        revision.message = u'Update package scores from cli'

        print "Packages..."

        packages = self._get_packages()
        
        if self.verbose:
            print "Total packages to update: " + str(len(packages))

        for package in packages:
            if self.verbose:
                print "Checking package", package.id, package.name
                for resource in package.resources:
                    print '\t%s' % (resource.url,)
            update_package_score(package,self.options.force)
            repo.commit()
            
        repo.commit_and_remove()
 
    def _get_packages(self):

        if len(self.args) > 1:
            packages = Session.query(Package).\
                       filter(Package.id==self.args[1]).all()
        else:
            start = self.options.start
            limit = int(self.options.limit) if self.options.limit else False
            
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
                    packages =  Session.query(Package).limit(limit).all()
                else:
                    packages =  Session.query(Package).all()

        return packages 
