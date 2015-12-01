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
