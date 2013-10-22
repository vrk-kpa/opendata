from ckan.lib.base import BaseController
from pylons import config

class QAController(BaseController):

    def __init__(self, *args, **kwargs):
        super(QAController, self).__init(*args, **kwargs)