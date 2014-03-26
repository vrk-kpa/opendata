import requests
import urlparse
import logging
import sys

from pylons import config

import ckan.plugins as p

REQUESTS_HEADER = {'content-type': 'application/json',
                   'User-Agent': 'ckanext-qa commands'}

class CkanApiError(Exception):
    pass


class QACommand(p.toolkit.CkanCommand):
    """
    QA analysis of CKAN resources

    Usage::

        paster qa init
           - Creates the database tables that QA expects for storing
           results

        paster qa [options] update [dataset/group name/id]
           - QA analysis on all resources in a given dataset, or on all
           datasets if no dataset given

        paster qa sniff {filepath}
           - Opens the file and determines its type by the contents

        paster qa view [dataset name/id]
           - See package score information

        paster qa clean
           - Remove all package score information

        paster qa migrate1
           - Migrates the way results are stored in task_status,
             with commit 6f63ab9e 20th March 2013
             (from key='openness_score'/'openness_score_failure_count' to
              key='status')

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster qa update --config=<path to CKAN config file>
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0

    def __init__(self, name):
        super(QACommand, self).__init__(name)
        self.parser.add_option('-q', '--queue',
                               action='store',
                               dest='queue',
                               help='Send to a particular queue')

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print QACommand.__doc__
            return

        cmd = self.args[0]
        self._load_config()

        # Now we can import ckan and create logger, knowing that loggers
        # won't get disabled
        self.log = logging.getLogger('ckanext.qa')

        from ckanext.qa.lib import get_site_url, get_user_and_context
        user, context = get_user_and_context(get_site_url(config))

        if cmd == 'update':
            self.update(user, context)
        elif cmd == 'sniff':
            self.sniff()
        elif cmd == 'view':
            if len(self.args) == 2:
                self.view(self.args[1])
            else:
                self.view()
        elif cmd == 'clean':
            self.clean()
        elif cmd == 'migrate1':
            self.migrate1()
        elif cmd == 'init':
            self.init_db()
        else:
            self.log.error('Command "%s" not recognized' % (cmd,))

    def init_db(self):
        import ckan.model as model
        from ckanext.qa.model import init_tables
        init_tables(model.meta.engine)

    def update(self, user, context):
        from ckan.model.types import make_uuid
        from ckan.lib.helpers import json
        # import tasks after load config so CKAN_CONFIG evironment variable
        # can be set
        import tasks

        for package in self._package_list():
            self.log.info('QA on dataset being added to Celery queue "%s": %s (%d resources)' % \
                        (self.options.queue, package.get('name'),
                         len(package.get('resources', []))))

            data = json.dumps(package)
            task_id = make_uuid()
            tasks.update_package.apply_async(args=[context, data],
                                             task_id=task_id,
                                             queue=self.options.queue)


    def _package_list(self):
        """
        Generate the package dicts as declared in self.args.

        Make API calls for the packages declared in self.args, and generate
        the package dicts.

        If no packages are declared in self.args, then retrieve all the
        packages from the catalogue.
        """
        from ckan.lib.helpers import json
        api_url = urlparse.urljoin(config.get('ckan.site_url_internally') or config['ckan.site_url'], 'api/action')
        if len(self.args) > 1:
            for id in self.args[1:]:
                # try arg as a group name
                url = api_url + '/organization_show'
                self.log.info('Requesting datasets in org %r', url)
                data = {'id': self.args[1],
                        'include_datasets': 1}
                response = requests.post(url, data=json.dumps(data), headers=REQUESTS_HEADER)
                if response.status_code == 200:
                    package_dicts = json.loads(response.text)['result']['packages']
                    package_names = [pd['name'] for pd in package_dicts]
                    if not self.options.queue:
                        self.options.queue = 'bulk'
                else:
                    # must be a package id
                    package_names = [id]
                    if not self.options.queue:
                        self.options.queue = 'priority'
                for package_name in sorted(package_names):
                    data = json.dumps({'id': unicode(package_name)})
                    url = api_url + '/package_show'
                    response = requests.post(url, data, headers=REQUESTS_HEADER)
                    if response.status_code == 403:
                        self.log.warning('Package "%s" is in the group but '
                                         'returned %i error, so skipping.' % \
                                         (package_name, response.status_code))
                        continue
                    elif not response.ok:
                        err = ('Failed to get package %s from url %r: %s %s' %
                               (package_name, url, response.status_code, response.reason))
                        self.log.error(err)
                        raise CkanApiError(err)
                    yield json.loads(response.content).get('result')
        else:
            if not self.options.queue:
                self.options.queue = 'bulk'
            page, limit = 1, 10
            while True:
                url = api_url + '/current_package_list_with_resources'
                response = requests.post(url,
                                         json.dumps({'page': page,
                                                     'limit': limit,
                                                     'order_by': 'name'}),
                                         headers=REQUESTS_HEADER)
                if not response.ok:
                    err = ('Failed to get package list with resources from url %r: %s %s' %
                           (url, response.status_code, response.reason))
                    self.log.error(err)
                    raise CkanApiError(err)
                chunk = json.loads(response.content).get('result')
                if not chunk:
                    break
                for package in chunk:
                    yield package
                page += 1

    def sniff(self):
        from ckanext.qa.sniff_format import sniff_file_format

        if len(self.args) < 2:
            print 'Not enough arguments', self.args
            sys.exit(1)
        for filepath in self.args[1:]:
            format_ = sniff_file_format(filepath, logging.getLogger('ckanext.qa.sniffer'))
            if format_:
                print 'Detected as: %s - %s' % (format_['display_name'], filepath)
            else:
                print 'ERROR: Could not recognise format of: %s' % filepath

    def view(self, package_ref=None):
        from ckan import model

        q = model.Session.query(model.TaskStatus).filter_by(task_type='qa')
        print 'QA records - %i TaskStatus rows' % q.count()
        print '      across %i Resources' % q.distinct('entity_id').count()

        if package_ref:
            pkg = model.Package.get(package_ref)
            print 'Package %s %s' % (pkg.name, pkg.id)
            for res in pkg.resources:
                print 'Resource %s' % res.id
                for row in q.filter_by(entity_id=res.id):
                    print '* %s = %r error=%r' % (row.key, row.value, row.error)

    def clean(self):
        from ckan import model

        print 'Before:'
        self.view()

        q = model.Session.query(model.TaskStatus).filter_by(task_type='qa')
        q.delete()
        model.Session.commit()

        print 'After:'
        self.view()

    def migrate1(self):
        from ckan import model
        from ckan.lib.helpers import json
        q_status = model.Session.query(model.TaskStatus) \
                   .filter_by(task_type='qa') \
                   .filter_by(key='status')
        print '* %s with "status" will be deleted e.g. %s' % (q_status.count(),
                                                              q_status.first())
        q_failures = model.Session.query(model.TaskStatus) \
                     .filter_by(task_type='qa') \
                     .filter_by(key='openness_score_failure_count')
        print '* %s with openness_score_failure_count to be deleted e.g.\n%s' % \
              (q_failures.count(), q_failures.first())
        q_score = model.Session.query(model.TaskStatus) \
                  .filter_by(task_type='qa') \
                  .filter_by(key='openness_score')
        print '* %s with openness_score to migrate e.g.\n%s' % (q_score.count(),
                                                                q_score.first())
        q_reason = model.Session.query(model.TaskStatus) \
                  .filter_by(task_type='qa') \
                  .filter_by(key='openness_score_reason')
        print '* %s with openness_score_reason to migrate e.g.\n%s' % (q_reason.count(),
                                                                       q_reason.first())
        raw_input('Press Enter to continue')

        q_status.delete()
        model.Session.commit()
        print '..."status" deleted'

        q_failures.delete()
        model.Session.commit()
        print '..."openness_score_failure_count" deleted'

        for task_status in q_score:
            reason_task_status = q_reason.filter_by(entity_id=task_status.entity_id).first()
            if reason_task_status:
                reason = reason_task_status.value
                reason_task_status.delete()
            else:
                reason = None

            task_status.key = 'status'
            task_status.error = json.dumps({
                'reason': reason,
                'format': None,
                'is_broken': None,
                })
            model.Session.commit()
        print '..."openness_score" and "openness_score_reason" migrated'

        count = q_reason.count()
        q_reason.delete()
        model.Session.commit()
        print '... %i remaining "openness_score_reason" deleted' % count

        model.Session.flush()
        model.Session.remove()
        print 'Migration succeeded'
