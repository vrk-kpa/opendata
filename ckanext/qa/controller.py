from ckan.model import Package, PackageExtra, Session
from ckan.lib.base import BaseController, c, g, request, \
                          response, session, render, config, abort

class QAController(BaseController):
    def index(self):                
        return render('ckanext/qa/index.html')
        
    def broken_packages(self):
        from pylons import tmpl_context as c
        c.broken_packages = []
        packages = Session.query(Package)
        for package in packages:
            if package.extras.get('openness_score') == 0.0:
                c.broken_packages.append(package)

        return render('ckanext/qa/broken_packages.html')