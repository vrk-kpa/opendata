from paste.script.command import Command

class PackageScore(Command):
    '''Manage the ratings stored in the db

    Usage:
      package-scores update         - update all package scores
      package-scores clean          - remove all package score information
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1
    parser = Command.standard_parser(verbose=False)

    def command(self):
        from ckan import model

        cmd = self.args[0]
        if cmd == 'update':
            self.update()
        elif cmd == 'clean':
            self.clean()
        else:
            sys.stderr.write('Command %s not recognized\n' % (cmd,))

    def clean(self, user_ratings=True):
        from ckan.model import Session, PackageExtra, repo
        from ckanext.qa.lib.package_scorer import PKGEXTRA

        revision = repo.new_revision()
        revision.author = u'cli script'
        revision.message = u'Update package scores from cli'

        for item in Session.query(PackageExtra).filter(PackageExtra.key.in_(PKGEXTRA)).all():
            item.purge()
        repo.commit_and_remove()

    def update(self, user_ratings=True):
        from ckan.model import Session, Package, repo
        from ckanext.qa.lib.package_scorer import update_package_score
        from ckanext.qa.lib.package_scorer import PKGEXTRA

        revision = repo.new_revision()
        revision.author = u'cli script'
        revision.message = u'Update package scores from cli'

        for package in Session.query(Package).all():
            if self.verbose:
                print "Checking package", package.id, package.name
                for resource in package.resources:
                    print '\t%s' % (resource.url,)
            update_package_score(package)
            repo.commit()
            
        repo.commit_and_remove()