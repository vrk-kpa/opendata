import logging

from ckan.lib.cli import CkanCommand


class InitDBCommand(CkanCommand):
    """
    Initialises the database with the required tables
    Connects to the CKAN database and creates the member request tables

    Usage:

        paster initdb
           - Creates the database table member request
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(InitDBCommand, self).__init__(name)

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        # if not self.args or self.args[0] in ['--help', '-h', 'help']:
        #    print self.usage
        #    sys.exit(1)

        # cmd = self.args[0]
        self._load_config()

        # Initialise logger after the config is loaded, so it is not disabled.
        self.log = logging.getLogger(__name__)

        # if cmd == 'initdb':
        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        import ckanext.ytp_request.model as rmodel
        self.log.info("Initializing tables")
        rmodel.init_tables()
        self.log.info("DB tables are setup")
        # else:
        #    self.log.error('Command %s not recognized' % (cmd,))
