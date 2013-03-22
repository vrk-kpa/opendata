import ckan.plugins.toolkit as t

from ckan.lib.base import render, c, BaseController, request, abort
from ckanext.qa.reports import (
    broken_resource_links_for_organisation,
    organisations_with_broken_resource_links,
    organisation_score_summaries,
    organisation_dataset_scores,
)

class QAOrganisationController(BaseController):
    def index(self):                
        return render('ckanext/qa/organisation/index.html')

    def broken_resource_links(self, id=None):
        try:
            c.include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        except ValueError:
            abort(400, 'include_sub_publishers parameter value must be boolean')
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
        try:
            c.include_sub_publishers = t.asbool(request.params.get('include_sub_publishers') or False)
        except ValueError:
            abort(400, 'include_sub_publishers parameter value must be boolean')
        if id is None:
            c.query = organisation_score_summaries
            c.organisations = c.query(include_sub_organisations=c.include_sub_publishers)
            return render('ckanext/qa/organisation/scores/index.html')
        else:
            c.org_name = id
            c.query = organisation_dataset_scores
            c.data = c.query(organisation_name=id, include_sub_organisations=c.include_sub_publishers)
            return render('ckanext/qa/organisation/scores/organisation.html')
