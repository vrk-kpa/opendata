import ckan.plugins.toolkit as t

from ckan.lib.base import render, c, BaseController, request
from ckanext.qa.reports import (
    broken_resource_links_for_organisation,
    organisations_with_broken_resource_links,
)

class QAOrganisationController(BaseController):
    def index(self):                
        return render('ckanext/qa/organisation/index.html')

    def broken_resource_links(self, id=None):
        c.include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        if id is None:
            c.query = organisations_with_broken_resource_links
            c.organisations = c.query(include_sub_organisations=c.include_sub_publishers)
            return render('ckanext/qa/organisation/broken_resource_links/index.html')
        else:
            c.org_name = id
            c.query = broken_resource_links_for_organisation
            c.data = c.query(organisation_name=id, include_sub_organisations=c.include_sub_publishers)
            return render('ckanext/qa/organisation/broken_resource_links/organisation.html')

    def scores(self, id=None):
        c.include_sub_publishers = t.asbool(request.params.get('include_sub_publishers', False))
        #TODO
        if id is None:
            c.organisations = organisations_with_broken_resource_links_by_name()
            return render('ckanext/qa/organisation/broken_resource_links/index.html')
        else:
            c.org_name = id
            c.data = broken_resource_links_by_dataset_for_organisation_detailed(organisation_name=id)
            c.query = broken_resource_links_by_dataset_for_organisation_detailed
            return render('ckanext/qa/organisation/broken_resource_links/organisation.html')
