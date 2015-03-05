import logging

from ckan.lib.cli import CkanCommand
from .model import init_tables

from pylons import config

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
        log = logging.getLogger(__name__)
        log.info("starting command")
        self._load_config()


        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        import ckanext.ytp.comments.model as cmodel
        log.info("Initializing tables")
        cmodel.init_tables()
        log.info("DB tables are setup")