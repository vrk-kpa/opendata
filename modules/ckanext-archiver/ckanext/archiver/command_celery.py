import sys
import os

from pkg_resources import iter_entry_points, VersionConflict
import ConfigParser
from celery import Celery

from ckan.lib.cli import CkanCommand


class CeleryCmd(CkanCommand):
    '''
    Manages the Celery daemons. This is an improved version of CKAN core's
    'celeryd' command.

    Usage:

        paster celeryd2 run [all|bulk|priority]
           - Runs a celery daemon to run tasks on the bulk or priority queue

    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2

    def __init__(self, name):
        super(CeleryCmd, self).__init__(name)
        self.parser.add_option('--loglevel',
                               action='store',
                               dest='loglevel',
                               default='INFO',
                               help='Celery logging - choose between DEBUG, INFO, WARNING, ERROR, CRITICAL or FATAL')
        self.parser.add_option('--concurrency',
                               action='store',
                               dest='concurrency',
                               default='1',
                               help='Number of concurrent processes to run')
        self.parser.add_option('-n', '--hostname',
                               action='store',
                               dest='hostname',
                               help="Set custom hostname")

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.usage
            sys.exit(1)

        cmd = self.args[0]
        # Don't need to load the config as the db is generally not needed
        #self._load_config()
        # But we do want to get the filename of the ini
        self._get_config()

        # Initialise logger after the config is loaded, so it is not disabled.
        #self.log = logging.getLogger(__name__)

        if cmd == 'run':
            queue = self.args[1]
            if queue=='all':
                queue = 'priority,bulk'
            self.run_(loglevel=self.options.loglevel,
                      queue=queue,
                      concurrency=int(self.options.concurrency),
                      hostname=self.options.hostname)
        else:
            print 'Command %s not recognized' % cmd
            sys.exit(1)

    def run_(self, loglevel='INFO', queue=None, concurrency=None,
             hostname=None):
        default_ini = os.path.join(os.getcwd(), 'development.ini')

        if self.options.config:
            os.environ['CKAN_CONFIG'] = os.path.abspath(self.options.config)
        elif os.path.isfile(default_ini):
            os.environ['CKAN_CONFIG'] = default_ini
        else:
            print 'No .ini specified and none was found in current directory'
            sys.exit(1)

        #from ckan.lib.celery_app import celery
        celery_args = []
        if concurrency:
            celery_args.append('--concurrency=%d' % concurrency)
        if queue:
            celery_args.append('--queues=%s' % queue)
        if self.options.hostname:
            celery_args.append('--hostname=%s' % hostname)
        celery_args.append('--loglevel=%s' % loglevel)

        argv = ['celeryd'] + celery_args
        print 'Running: %s' % ' '.join(argv)
        celery_app = self._celery_app()
        celery_app.worker_main(argv=argv)

    def _celery_app(self):
        # reread the ckan ini using ConfigParser so that we can get at the
        # non-pylons sections
        config = ConfigParser.ConfigParser()
        config.read(self.filename)

        celery_config = dict(
            CELERY_RESULT_SERIALIZER='json',
            CELERY_TASK_SERIALIZER='json',
            CELERY_IMPORTS=[],
        )

        for entry_point in iter_entry_points(group='ckan.celery_task'):
            try:
                celery_config['CELERY_IMPORTS'].extend(
                    entry_point.load()()
                )
            except VersionConflict, e:
                error = 'ERROR in entry point load: %s %s' % (entry_point, e)
                print error
                pass

        LIST_PARAMS = 'CELERY_IMPORTS ADMINS ROUTES'.split()
        try:
            for key, value in config.items('app:celery'):
                celery_config[key.upper()] = value.split() \
                    if key in LIST_PARAMS else value
        except ConfigParser.NoSectionError:
            error = 'Could not find celery config in your ckan ini file (a section headed "[app:celery]".'
            print error
            sys.exit(1)

        celery_app = Celery()
        # Thes update of configuration means it is only possible to set each
        # key once so this is done once all of the options have been decided.
        celery_app.conf.update(celery_config)
        celery_app.loader.conf.update(celery_config)
        return celery_app
