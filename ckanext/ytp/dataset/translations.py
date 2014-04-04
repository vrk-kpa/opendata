
def _translations():
    """ Does nothing but hints message extractor to extract missing strings. """
    from ckan.common import _
    _("Valid from")
    _("Valid till")
    _("Title en")
    _("Title fi")
    _("Title sv")


def facet_translations():
    return ["Open Data", "Interoperability Tools", "Public Service"]
