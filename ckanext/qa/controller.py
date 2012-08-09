import ckan.plugins as p
from pylons import config
from paste.deploy.converters import asbool

from ckan.lib.base import BaseController

class QAController(BaseController):
    def index(self):
        p.toolkit.c.organisations = asbool(config.get('qa.organisations', True))
        return p.toolkit.render('ckanext/qa/index.html')
