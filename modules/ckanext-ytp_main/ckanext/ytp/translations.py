

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

def facet_translations():
    return ["Open Data", "Interoperability Tools", "Public Service", "External", "Internal"]

