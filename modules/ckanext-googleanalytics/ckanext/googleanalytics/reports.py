googleanalytics_report_info = {
    'name': 'analytics',
    'description': 'Analytics showing resource views',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': broken_links_option_combinations,
    'generate': broken_links,
    'template': 'report/broken_links.html',
    }


openness_report_info = {
    'name': 'openness',
    'title': 'Openness (Five Stars)',
    'description': 'Datasets graded on Tim Berners Lees\' Five Stars of Openness - openly licensed, openly accessible, structured, open format, URIs for entities, linked.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': openness_report_combinations,
    'generate': openness_report,
    'template': 'report/openness.html',
    }
