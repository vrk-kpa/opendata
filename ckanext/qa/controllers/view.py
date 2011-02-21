from ckan.lib.base import BaseController, c, g, request, \
                          response, session, render, config, abort
from ..dictization import *

class ViewController(BaseController):
    
    def index(self):                
        return render('ckanext/qa/index.html')

    def package_openness_scores(self):
        c.packages = package_openness_score()
        return render('ckanext/qa/package_openness_scores.html')

    def packages_with_broken_resource_links(self):
        c.packages = packages_with_minimum_one_broken_resource()
        return render('ckanext/qa/packages_with_broken_resource_links.html')
