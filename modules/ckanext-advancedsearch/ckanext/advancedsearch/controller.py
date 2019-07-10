import ckan.lib.base as base
from ckan.lib.base import render


class YtpAdvancedSearchController(base.BaseController):
    def search(self):
        return render('advanced_search/read.html', extra_vars={"options": [
            {"value": "1", "label": u"Alueet ja kaupungit"},
            {"value": "2", "label": u"Energia"},
            {"value": "3", "label": u"Hallinto ja julkinen sektori"},
            {"value": "4", "label": u"Kansainvaliset asiat"},
            {"value": "5", "label": u"Koulutus"},
            {"value": "6", "label": u"Liikenne"},
            {"value": "7", "label": u"Paras kategoria"},
            {"value": "8", "label": u"Speciaali"},
        ]})
