from pylons import config
from paste.deploy.converters import asbool
from ckan.lib.base import BaseController, c, render


class QAHomeController(BaseController):
    def index(self):
        c.organisations = asbool(config.get('qa.organisations', True))
        return render('ckanext/qa/index.html')
