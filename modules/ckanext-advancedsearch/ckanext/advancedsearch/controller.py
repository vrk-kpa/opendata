import ckan.lib.base as base
from ckan.lib.base import render


class YtpAdvancedSearchController(base.BaseController):
    def search(self):
        return render('advanced_search/index.html')
