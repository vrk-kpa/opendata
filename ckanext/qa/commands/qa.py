import sys
import os
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.logic.action import get
from ckan import model
from ckan.model import Session, Package, repo
from ckanext.qa.lib.package_scorer import package_score
from ckanext.qa.lib.log import log, set_config

# Use this specific author so that these revisions can be filtered out of
# normal RSS feeds that cover significant package changes. See DGU#982.
MAINTENANCE_AUTHOR = u'okfn_maintenance'

class QA(CkanCommand):
    """Manage the ratings stored in the db

    Usage::

        paster qa [options] update [{package-id}]
           - Update all package scores or just one if a package id is provided

        paster qa clean        
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

        paster qa update --config=../ckan/development.ini

    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2 
    min_args = 0

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
            print QA.__doc__
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
            sys.stderr.write('Command %s not recognized\n' % (cmd,))

    def clean(self):
        """
        Remove all archived resources.
        """
        log.error("QA Clean: No longer functional")
        # revision = repo.new_revision()
        # revision.author = MAINTENANCE_AUTHOR
        # revision.message = u'Update package scores from cli'
        # for item in Session.query(PackageExtra).filter(PackageExtra.key.in_(PKGEXTRA)).all():
        #     item.purge()
        # repo.commit_and_remove()

    def update(self, package_id = None):
        # check that archive folder exists
        if not os.path.exists(self.archive_folder):
            log.error("No archived files found.")
            log.error("Check that the archive path is correct and run the archive command")
            return
        results_file = os.path.join(self.archive_folder, 'archive.db')
        context = {'model': model, 'user': MAINTENANCE_AUTHOR}

        if package_id:
            context['id'] = package_id
            package = get.package_show(context)
            if package:
                packages = [package]
            else:
                log.info("Error: Package not found: %s" % package_id)
        else:
            start = self.options.start
            limit = int(self.options.limit or 0)
            if start:
                # ids = Session.query(Package.id).order_by(Package.id).all()
                # index = [i for i,v in enumerate(ids) if v[0] == start]
                # if not index:
                #     log.error('Error: Package not found: %s' % start)
                #     sys.exit()
                # if limit is not False:
                #     ids = ids[index[0]:index[0] + limit]
                # else:
                #     ids = ids[index[0]:]
                # packages = [Session.query(Package).filter(Package.id == id[0]).first() for id in ids]
                log.error("Start parameter is not currently implemented")
            else:
                if limit:
                    context['limit'] = limit
                    log.info("Limiting results to %d packages" % limit)
                packages = get.current_package_list_with_resources(context)

        log.info("Total packages to update: %d" % len(packages))
        if not packages:
            return

        for package in packages:
            resources = package.get('resources', [])
            if not len(resources):
                log.info("Package %s has no resources - skipping" % package['name'])
            else:
                log.info("Checking package: %s (%d resource(s))" % 
                    (package['name'], len(resources))
                )
                package_score(package, results_file) 
