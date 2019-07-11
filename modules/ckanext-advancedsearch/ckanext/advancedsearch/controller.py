import ckan.lib.base as base
from ckan.lib.base import render


class YtpAdvancedSearchController(base.BaseController):
    def search(self):
        # TODO: Get the input fields from a schema file
        return render(
            'advanced_search/index.html',
            extra_vars={
                "input_fields": {
                    "search_term": {
                        "field_name": "search_term",
                        "label": "Hakusanat",
                        "display_snippet": "search-bar.html",
                        "display_options": {
                            "placeholder": "Kirjoita mita olet etsimassa",
                        }
                    },
                    "search_target": {
                        "field_name": "search_target",
                        "label": "Haun kohdistuminen",
                        "options": [
                            {"value": "1", "label": u"All"},
                            {"value": "2", "label": u"Vain otsikko"},
                            {"value": "3", "label": u"Vain kuvaus"},
                        ],
                        "display_snippet": "radio-select.html",
                    },
                    "category": {
                        "field_name": "category",
                        "label": "Kategoria",
                        "options": [
                            {"value": "1", "label": u"Alueet ja kaupungit"},
                            {"value": "2", "label": u"Energia"},
                            {"value": "3", "label": u"Hallinto ja julkinen sektori"},
                            {"value": "4", "label": u"Kansainvaliset asiat"},
                            {"value": "5", "label": u"Koulutus"},
                            {"value": "6", "label": u"Liikenne"},
                            {"value": "7", "label": u"Paras kategoria"},
                            {"value": "8", "label": u"Speciaali"},
                        ],
                        "display_snippet": "multiselect.html",
                        "display_options": {
                            "allow_select_all": True,
                        }
                    },
                    "publisher": {
                        "field_name": "publisher",
                        "label": "Julkaisija",
                        "options": [
                            {"value": "1", "label": "Helsingin kaupunki"},
                            {"value": "2", "label": "Helsingin Kuntayhtyma"},
                            {"value": "3", "label": "Helluntaiseurakunta"},
                            {"value": "4", "label": "Hellun Kanat"},
                            {"value": "5", "label": "Hellat tunteet RY"},
                        ],
                        "display_snippet": "multiselect.html",
                        "display_options": {
                            "allow_select_all": True,
                        }
                    },
                    "licence": {
                        "field_name": "licence",
                        "label": "Lisenssi",
                        "options": [
                            {"value": "1", "label": "CC0 1.0"},
                            {"value": "2", "label": "Creative Commons 4.0"},
                            {"value": "3", "label": "Open database license 1.0"},
                            {"value": "4", "label": "Other (non commercial)"},
                            {"value": "5", "label": "Other (non option)"},
                        ],
                        "display_snippet": "multiselect.html",
                        "display_options": {
                            "allow_select_all": True,
                        }
                    },
                    "format": {
                        "field_name": "format",
                        "label": "Formaatti",
                        "options": [
                            {"value": "1", "label": "API"},
                            {"value": "2", "label": "CSV"},
                            {"value": "3", "label": "CSV / ZIP"},
                            {"value": "4", "label": "Database"},
                            {"value": "5", "label": "DOC"},
                            {"value": "6", "label": "ESRI REST"},
                            {"value": "7", "label": "GEOJSON"},
                        ],
                        "display_snippet": "multiselect.html",
                        "display_options": {
                            "allow_select_all": False,
                        }
                    },
                    "released": {
                        "field_name": "released",
                        "label": "Julkaisu paiva",
                        "display_snippet": "datepicker-range.html",
                        "display_options": {
                            "label": {
                                "start": "Julkaistu ennen",
                                "end": "Julkaistu jalkeen",
                            }
                        }
                    },
                    "updated": {
                        "field_name": "updated",
                        "label": "Paivitys paiva",
                        "display_snippet": "datepicker-range.html",
                        "display_options": {
                            "label": {
                                "start": "Paivitetty ennen",
                                "end": "Paivitetty jalkeen",
                            }
                        }
                    },
                }
            }
        )
