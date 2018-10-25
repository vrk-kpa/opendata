def _translations():
    """ Does nothing but hints message extractor to extract missing strings. """
    from ckan.common import _, ungettext
    _("An URL-address which refers to the dataset. The automatically filled option derived"
      " from the title is the best option in most cases.")
    _("Category which represents showcase.")
    _("Platforms of the showcase.")
    _("Keywords or tags through which users are able to find this dataset easily through the"
      " search page or other datasets which have the same tag.")
    _("Author Website")
    _("Application Website")
    _("Links to stores")
    _("Kuvaus")
    _("An universal, compact and easy to understand description of the added resource.")
    _("Featured")
    _("Icon")
    _("Featured Image")
    _("Image 1")
    _("Image 2")
    _("Image 3")
    _("Notifier")
    _("Notifier Email")
    _("eg. android")
    _("eg. visualization")
    _("eg. traffic")
    ungettext("The dataset has been added to the showcase.", "The datasets have been added to the showcase.", 2)
    ungettext("The dataset has been removed from the showcase.", "The datasets have been removed from the showcase.", 2)
