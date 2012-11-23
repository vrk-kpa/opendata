from ckan.lib.base import render, c, request
from ckanext.qa.reports import broken_resource_links_by_dataset
from base import QAController

class QAPackageController(QAController):
    
    def index(self):                
        return render('ckanext/qa/dataset/index.html')

    # openness by dataset is removed since it was unmanageable with 8000
    # datasets. Add back, but with paging this time?

    def broken_resource_links(self):
        c.packages = broken_resource_links_by_dataset()
        return render('ckanext/qa/dataset/broken_resource_links/index.html')
