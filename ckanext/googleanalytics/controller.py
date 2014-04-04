import logging
from ckan.lib.base import BaseController, c, render
import dbutil

log = logging.getLogger('ckanext.googleanalytics')

class GAController(BaseController):
    def view(self):
        # get package objects corresponding to popular GA content
        c.top_packages = dbutil.get_top_packages(limit=10)
        c.top_resources = dbutil.get_top_resources(limit=10)
        return render('summary.html')
