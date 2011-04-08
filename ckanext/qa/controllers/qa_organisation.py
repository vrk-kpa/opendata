from ckan.lib.base import BaseController, render, c
from ..dictization import (
    organisations_with_broken_resource_links, 
    broken_resource_links_by_package_for_organisation,
)

class QAOrganisationController(BaseController):
    
    def index(self):                
        return render('ckanext/qa/organisation/index.html')

    def broken_resource_links(self, id=None):
        if id is None:
            c.organisations = organisations_with_broken_resource_links()
            return render('ckanext/qa/organisation/broken_resource_links/index.html')
        else:
            c.id = id
            c.organisation = broken_resource_links_by_package_for_organisation(organisation_id=id)
            return render('ckanext/qa/organisation/broken_resource_links/organisation.html')

