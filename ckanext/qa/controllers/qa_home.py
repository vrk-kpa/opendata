from ckan.lib.base import BaseController, render

class QAHomeController(BaseController):
    
    def index(self):                
        return render('ckanext/qa/index.html')


