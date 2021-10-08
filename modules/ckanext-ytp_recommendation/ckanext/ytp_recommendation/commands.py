import ckan.model as model
from ckan.lib.cli import CkanCommand

from ckanext.ytp_recommendation.model import init_tables


class RecommendationCommand(CkanCommand):
    '''
    Usage:
        paster recommendations init
            - Initializes database tables used by ytp_recommendations.
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 1

    def command(self):
        cmd = self.args[0]
        self._load_config()

        if cmd == 'init':
            self.initdb()
        else:
            self.log.error('Command "%s" not recognized' % (cmd,))

    def initdb(self):
        init_tables(model.meta.engine)
