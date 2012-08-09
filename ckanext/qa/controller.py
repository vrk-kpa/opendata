from pylons import config

import ckan.plugins as p
from ckan.lib.base import BaseController

from ckanext.qa.reports import (
    organisations_with_broken_resource_links_by_name,
    broken_resource_links_by_dataset_for_organisation,
    five_stars, broken_resource_links_by_dataset,
)

c = p.toolkit.c
render = p.toolkit.render

class QAController(BaseController):
    def index(self):
        c.organisations = p.toolkit.asbool(config.get('qa.organisations', True))
        return render('ckanext/qa/index.html')

    def package_index(self):
        return render('ckanext/qa/dataset/index.html')

    def five_stars(self):
        c.packages = five_stars()
        return p.toolkit.render('ckanext/qa/dataset/five_stars/index.html')

    def broken_resource_links(self):
        c.packages = broken_resource_links_by_dataset()
        return render('ckanext/qa/dataset/broken_resource_links/index.html')

    def organisation_index(self):
        return render('ckanext/qa/organisation/index.html')

    def broken_resource_links(self, id=None):
        if id is None:
            c.organisations = organisations_with_broken_resource_links_by_name()
            return render('ckanext/qa/organisation/broken_resource_links/index.html')
        else:
            c.id = id
            c.organisation = broken_resource_links_by_dataset_for_organisation(organisation_id=id)
            return render('ckanext/qa/organisation/broken_resource_links/organisation.html')
