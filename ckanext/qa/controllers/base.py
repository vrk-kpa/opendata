from pylons import c

from ckan.lib.base import BaseController

class QAController(BaseController):
    def __call__(self, environ, start_response):
        # turns off sidebar in DGU theme
        c.hide_sidebar = True
        
        return super(QAController, self).__call__(environ, start_response)
