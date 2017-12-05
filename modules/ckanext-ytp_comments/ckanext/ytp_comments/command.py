import logging

from ckan.lib.cli import CkanCommand


class InitDBCommand(CkanCommand):
    """
    Initialises the database with the required tables
    Connects to the CKAN database and creates the comment
    and thread tables ready for use.
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(InitDBCommand, self).__init__(name)

    def command(self):

        self._load_config()

        # Initialise logger after the config is loaded, so it is not disabled.
        self.log = logging.getLogger(__name__)

        self.log.info("starting command")

        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        import ckanext.ytp_comments.model as cmodel
        self.log.info("Initializing tables")
        cmodel.init_tables()
        self.log.info("DB tables are setup")
