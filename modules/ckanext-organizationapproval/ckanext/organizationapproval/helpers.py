from ckan.lib import helpers


def make_pager_url(q=None, page=None):
    ctrlr = 'ckanext.organizationapproval.controller:OrganizationApprovalController'
    url = helpers.url_for(controller=ctrlr, action='manage_organizations')
    return url + u'?page=' + str(page)
