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
    _('Created')

    _("URL")
    _("Title")
    _("Image URL")
    _("Image")
    _("Size")
    _("Formats")
    _("Organization")
    _("Key")

    _('Fullname')
    _('International benchmarks')
    _('eg. Maps')
    _('A short and descriptive title for the dataset. Do not utilize dates in the title but instead '
      'add multiple time-specific resources to the dataset in the next stage.')
    _('A short and descriptive name for the resource.')
    _('Size of the added resouce file in bytes. Will be automatically filled when the file is uploaded.')
    _('File format of the selected resource.')
    _('An universal, compact and easy to understand description of the added dataset. Use as confining terms as possible '
      'to assist the user to understand what types of data, meters and dimensions the dataset contains.')
    _('Coordinates which describe the area which the added resource is associated with.')
    _('The origin of the dataset.')
    _('eg. A detailed description')
    _('eg. every second week')
    _('Collection type')
    _('Maintainer email')
    _('Author email')
    _('Maintainer website')
    _('Select international benchmarks which this dataset belongs to.')
    _('Private datasets will only be seen by the logged in users of the dataset\'s organization. Public datasets '
      'will be listed publicly through the search.')
    _('The organization which owns the dataset.')
    _('A moment in time after which the data is relevant.')
    _('A moment in time after which the data is no longer relevant.')
    _('A string which describes the precision of the entered time series.')
    _('eg. 2 weeks')
    _('eg. joe@example.com')

    _('Copyright notice')
    _('Geographical coverage')
    _('Select the municipalities from which the dataset contains data.')
    _('Links to additional information')
    _('Links to additional information concerning the dataset.')
    _('Update frequency')
    _('A short description of how frequently the dataset will get updated.')
    _('Features')
    _('Members can only edit their own datasets')
    _('Home page')
    _('Maturity')
    _('Position coordinates')
    _('Time series start')
    _('Time series end')
    _('Time series precision')
    _('Temporal granularity')
    _('Temporal coverage from')
    _('Temporal coverage to')
    _('Showcase name')
    _('Categories')
    _('Producer type')
    _('Public administration organization')

    # Values
    _('public_administration_organization')
    _('personal_datasets')
    _('State administration')
    _('Country')
    _('Region')
    _('Open Data')
    _('Interoperability Tools')
    _('Public service')
    _('Cities')
    _('Education - Research')
    _('Enterprise')
    _('Person')
    _('Society - Trust')
    _('active')
    _('deleted')
    _('draft')
    _('Current version')
    _('Archived version')
    _('Draft version')

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
    _('Broken links')
    _('Dataset resource URLs that are found to result in errors when resolved.')
    _('Openness (Five Stars)')
    _('Datasets graded on Tim Berners-Lee\'s Five Stars of Openness - openly licensed, '
      'openly accessible, structured, open format, URIs for entities, linked.')
    _('Deprecated datasets')
    _('Datasets that have deprecated')
    _('Google analytics showing most audience locations (bot traffic is filtered out)')
    _('Least popular datasets')
    _('Google analytics showing top datasets with least views')
    _('Most popular datasets')
    _('Google analytics showing top datasets with most views')
    _('Most popular organizations')
    _('Google analytics showing most popular organizations by visited datasets')
    _('Most popular resources')
    _('Google analytics showing most downloaded resources')
    _('Most popular search terms')
    _('Google analytics showing most popular search terms')
    _('Harvester status')
    _('Harvester statuses')
    _('No jobs yet')

    # Hierarchy
    _('The dataset amount of the organization is shown beside the organization name.')
    _('Organizations with no datasets are shown in this list only when using the search functionality')
    _('None - top level')
    _('Parent organization')

    # Messages generated by actions, not available in our code base
    _('Organization cannot be deleted while it still has datasets')

    # Translations for keys from schema
    _("fi")
    _("en")
    _("sv")

    # Dataset
    _("Dataset title")
    _("e.g. Finnish names")
    _("Give a short and descriptive name for the dataset.")
    _("The URL is created automatically based on the dataset title. You can edit the URL if you want.")
    _("Give a short and descriptive name for the dataset.<br><br>The URL is created automatically based on the dataset title. You can edit the URL if you want.")  # noqa: E501
    _("Dataset description")
    _("Write a description for the dataset.")
    _("Describe the dataset’s contents, collection process, quality and  possible limits, flaws and applications in a comprehensible way. Use as confining terms as possible to make it easier to find and understand the data.")  # noqa: E501
    _("Keywords help users to find your data. Select at least one keyword in Finnish.")  # noqa: E501
    _("Select at least one category.")
    _("Dataset additional information")
    _("Dataset visibility")
    _("You can set the visibility to private temporarily for example if the dataset is missing some information. Private datasets are visible to all members of the producer-organisation.")  # noqa: E501
    _("Select a license that suits your needs. We recommend using CC0 or CC BY 4 -licenses.")
    _("More about the license")
    _("Describe how you want your organisation to be named when using CC BY 4 -license.")
    _("e.g. Data was produced by Finnish Digital Agency")
    _("Select which municipalities/cities the data covers.")
    _("e.g. Tampere")
    _("Describe how often your data is updated")
    _("e.g. monthly")
    _("Add links to one or more websites with additional information about the data.")
    _("Select the dataset publisher (organisation).")
    _("Dataset producer and maintainer")
    _("Dataset maintainer")
    _("The dataset maintainer will receive updates about the dataset to the email address specified in this form. We recommend using a general email address instead of the contact information of a single employee. Note that the dataset information can only be managed by registered users with Editor- or Admin-rights in the publishing organisation.")  # noqa: E501
    _("e.g. avoindata@dvv.fi")

    # Resource
    _("Data resource title")
    _("Write a short and descriptive name for the data resource. If the data covers a specific time frame, mention that in the name.")  # noqa: E501
    _("e.g. Most popular Finnish first names 2019")
    _("Resource *")
    _("Add the data resource by uploading a file or adding a link to the data.<br>Select or drag the files here.<br>The maximum file size is 5 Gb. Valid data formats are pdf, jpg, jpeg, png, doc, docx, xls, xlsx, csv, ppt, pptx, odt, ods, txt.<br>Link: Add a link to the data.")  # noqa: E501
    _("Data resource description")
    _("Write a description for the resource")
    _("Describe the data clearly and concisely. Use as confining terms as possible to make it easier to find and understand the data.")  # noqa: E501
    _("Additional information")
    _("Data status")
    _("Define a state for the data. This is recommended especially if your dataset has data resources from multiple years.")
    _("Coordinate system")
    _("If your data includes geographic information, specify the coordinate system it uses.")
    _("e.g. WGS84 (World Geodetic System 1984)")
    _("Select the time frame by which the data is separated. For example, does the resource include data from every week or month.")  # noqa: E501
    _("e.g. a month")
    _("Time Frame")
    _("Start date")
    _("End date")

    # Licenses
    _('cc-by')
    _('cc-by-4-fi')
    _('cc-by-4.0')
    _('cc-by-sa')
    _('cc-by-sa-1-fi')
    _('cc-nc')
    _('cc-zero')
    _('cc-zero-1.0')
    _('gfdl')
    _('helsinkikanava-opendata-tos')
    _('hri-tietoaineistot-lisenssi-nimea')
    _('ilmoitettumuualla')
    _('kmo-aluejakorajat')
    _('notspecified')
    _('odc-by')
    _('odc-odbl')
    _('odc-pddl')
    _('other')
    _('other-at')
    _('other-closed')
    _('other-nc')
    _('other-open')
    _('other-pd')
    _('uk-ogl')

    # Showcase
    _('Platforms')

    # Facet filter "Show more ..." texts
    _('Show more collection_type')
    _('Show more vocab_international_benchmarks')
    _('Show more vocab_keywords_en')
    _('Show more vocab_keywords_fi')
    _('Show more vocab_keywords_sv')
    _('Show more organization')
    _('Show more res_format')
    _('Show more source')
    _('Show more license_id')
    _('Show more groups')
    _('Show more vocab_platform')

    # Facet filter "Show less ..." texts
    _('Show less collection_type')
    _('Show less vocab_international_benchmarks')
    _('Show less vocab_keywords_en')
    _('Show less vocab_keywords_fi')
    _('Show less vocab_keywords_sv')
    _('Show less organization')
    _('Show less res_format')
    _('Show less source')
    _('Show less license_id')
    _('Show less groups')
    _('Show less vocab_platform')


def facet_translations():
    return ["Open Data", "Interoperability Tools", "External", "Internal"]
