from ckan.lib.base import BaseController, c, g, request, response, session, render, config, abort

class QAController(BaseController):
    def index(self):
        from pylons import tmpl_context as c
        c.broken_packages = []
        return render('ckanext/qa/index.html')