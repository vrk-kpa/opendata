from ckan.lib.base import BaseController, render, c
from ..dictization import five_stars, broken_resource_links_by_package

class QAPackageController(BaseController):
    
    def index(self):                
        return render('ckanext/qa/package/index.html')

    def five_stars(self):
        c.packages = five_stars()
        return render('ckanext/qa/package/five_stars/index.html')

    def broken_resource_links(self):
        c.packages = broken_resource_links_by_package()
        return render('ckanext/qa/package/broken_resource_links/index.html')
        
