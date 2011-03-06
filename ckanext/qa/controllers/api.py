import json
from ckan.lib.base import BaseController, c, g, request, \
                          response, session, render, config, abort
from ..dictization import *

class ApiController(BaseController):
                
    def package_openness_scores(self, id=None):
        return json.dumps(package_openness_score(package_id=id))
        
    def packages_with_broken_resource_links(self, id=None, name=None):
        return json.dumps(packages_with_minimum_one_broken_resource(
            organization_id=id, organization_name=name
        ))
