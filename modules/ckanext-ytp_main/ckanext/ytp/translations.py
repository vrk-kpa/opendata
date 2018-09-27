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
    _('A short and descriptive title for the dataset. Do not utilize dates in the title but instead '
      ' add multiple time-specific resources to the dataset in the next stage.')
    _('An universal, compact and easy to understand description of the added dataset. Use as confining terms as possible '
      'to assist the user to understand what types of data, meters and dimensions the dataset contains.')
    _('eg. A detailed description')
    _('eg. every second week')
    _('Collection type')
    _('Maintainer email')
    _('Author email')
    _('Maintainer website')
    _('Select high value dataset categories which this dataset belongs to')
    _('Private datasets will only be seen by the logged in users of the dataset\'s organization. Public datasets '
      'will be listed publicly through the search.')
    _('The organization which owns the dataset.')
    _('Copyright notice')
    _('An universal, compact and easy to understand description of the added dataset. Use as confining terms as possible '
      'to assist the user to understand what types of data, meters and dimensions the dataset contains.')
    _('Geographical coverage')
    _('Select the municipalities from which the dataset contains data.')
    _('Links to additional information')
    _('Links to additional information concerning the dataset.')
    _('Update frequency')
    _('A short description of how frequently the dataset will get updated.')
    _('Features')
    _('Members can only edit their own datasets')
    _('Home page')

    # Values
    _('public_administration_organization')
    _('personal_datasets')
    _('civil-service')
    _('municipality')
    _('other-public-service')
    _('educational-research-institute')
    _('company')
    _('individual')
    _('association')

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
    _('Groups')
    _('A little information about my group...')
    _('Create a Group')
    _('Create Group')
    _('My Group')

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

    # Reports
    _('Administrative Branch Summary')
    _('Dataset statistics by administrative branch summary')


def facet_translations():
    return ["Open Data", "Interoperability Tools", "Public Service", "External", "Internal"]
