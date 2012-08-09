from pylons import config

import ckan.plugins as p
from ckan.lib.base import BaseController

from ckanext.qa.reports import five_stars, broken_resource_links_by_dataset

class QAController(BaseController):
    def index(self):
        p.toolkit.c.organisations = p.toolkit.asbool(config.get('qa.organisations', True))
        return p.toolkit.render('ckanext/qa/index.html')

    def package_index(self):
        return p.toolkit.render('ckanext/qa/dataset/index.html')

    def five_stars(self):
        p.toolkit.c.packages = five_stars()
        return p.toolkit.render('ckanext/qa/dataset/five_stars/index.html')

    def broken_resource_links(self):
        p.toolkit.c.packages = broken_resource_links_by_dataset()
        return p.toolkit.render('ckanext/qa/dataset/broken_resource_links/index.html')
