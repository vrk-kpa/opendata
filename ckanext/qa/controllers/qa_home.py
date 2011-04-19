from ckan.lib.base import render
from base import QAController

class QAHomeController(QAController):
    
    def index(self):
        return render('ckanext/qa/index.html')


