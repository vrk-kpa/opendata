from ckan.lib.base import BaseController, c, g, request, \
                          response, session, render, config, abort
from pprint import pprint
from ..dictization import *

class ViewController(BaseController):
    
    def index(self):                
        return render('ckanext/qa/index.html')

    def package_openness_scores(self):
        c.packages = package_openness_score()
        return render('ckanext/qa/package_openness_scores.html')

    def packages_with_broken_resource_links(self):
        c.organisations = packages_by_organisation_with_minimum_one_broken_resource()
        #raise Exception(c.packages)
        #raise Exception(c.packages[(u'11401', u'Department for Communities and Local Government')])
        return render('ckanext/qa/packages_with_broken_resource_links.html')
        
    def organizations_with_broken_resource_links(self, id=None):
        if id:
            c.id = id
            c.packages = packages_with_minimum_one_broken_resource(organization_id=c.id)
            return render('ckanext/qa/organizations_broken_resource_links.html')
        else:
            c.packages = packages_with_minimum_one_broken_resource()
            return render('ckanext/qa/organizations_index.html')

