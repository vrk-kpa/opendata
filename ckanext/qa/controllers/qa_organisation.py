from ckan.lib.base import render, c
from ckanext.qa.reports import (
    organisations_with_broken_resource_links_by_name, 
    broken_resource_links_by_dataset_for_organisation_detailed,
)
from base import QAController

class QAOrganisationController(QAController):
    
    def index(self):                
        return render('ckanext/qa/organisation/index.html')

    def broken_resource_links(self, id=None):
        if id is None:
            c.organisations = organisations_with_broken_resource_links_by_name()
            return render('ckanext/qa/organisation/broken_resource_links/index.html')
        else:
            c.org_name = id
            c.data = broken_resource_links_by_dataset_for_organisation_detailed(organisation_name=id)
            return render('ckanext/qa/organisation/broken_resource_links/organisation.html')

