# -*- coding: utf-8 -*-

def _translations():
    """ Does nothing but hints message extractor to extract missing strings. """
    from ckan.common import _
    # Dataset error labels (converted field names)
    _("Valid from")
    _("Valid till")
    _("Title en")
    _("Title fi")
    _("Title sv")
    _("Tag string")
    _("Notes")
    _("Content type")
    _("Owner org")

    # dataset licences and urls
    _('Creative Commons Attribution 4.0')
    _('http://creativecommons.org/licenses/by/4.0/')
    _('http://creativecommons.org/publicdomain/zero/1.0/')

    # Missing from CKAN translation
    _('File upload too large')

    _('External')
    _('Internal')

    _("URL")
    _("Title")
    _("Image URL")
    _("Image")
    _("Formats")
    _("Organization")

    _('Fullname')
    _('High value dataset category')
    _('eg. Maps')

    # Assets common terms
    _('Log in')
    _('Log out')
    _('Publish Datasets')
    _('News')
    _('About us')
    _('Files')
    _('Guide to Open Data')
    _('User Info')
    _('Training')
    _('Dataset is available at http://www.syke.fi/avointieto')
    _('Apps')

    # Group renaming
    _('Add to group')
    _('There are no groups associated with this dataset')
    _('Remove dataset from this group')
    _('Associate this group with this dataset')
    _('Add Group')
    _('There are currently no groups for this site')
    _('Search groups...')
    
    # Administrative Branches
    _('Liikenne- ja viestintäministeriö\'s administrative branch')
    _('Maa- ja metsätalousministeriö\'s administrative branch')
    _('Oikeusministeriö\'s administrative branch')
    _('Opetus- ja kulttuuriministeriö\'s administrative branch')
    _('Puolustusministeriö\'s administrative branch')
    _('Sisäministeriö\'s administrative branch')
    _('Sosiaali- ja terveysministeriö\'s administrative branch')
    _('Työ- ja elinkeinoministeriö\'s administrative branch')
    _('Valtioneuvoston kanslia\'s administrative branch')
    _('Valtiovarainministeriö\'s administrative branch')
    _('Ympäristöministeriö\'s administrative branch')
    _('Ulkoministeriö\'s administrative branch')

def facet_translations():
    return ["Open Data", "Interoperability Tools", "Public Service", "External", "Internal"]

