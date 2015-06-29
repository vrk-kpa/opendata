import ckan.plugins as p


class IReport(p.Interface):
    """
    Allows a plugin to register some functions for generating reports
    that are too expensive to perform at run-time.
    """

    def register_reports(self):
        """
        Register details of an extension's reports. Each report, with any
        specified combinations of options, will be run regularly (by setting up
        a cron running "paster report-cache generate". The report results are
        then stored in a cache, making them quick to view by end-users.

        This method should return a list of dicts, each one describing a
        report. A report dict looks like:
        {
            'name': 'feedback-report',
            'option_defaults': OrderedDict((('publisher', None),
                                            ('include_sub_publishers', False),
                                            ('include_published', False))),
                          # OrderedDict of default option values, when none are
                          # specified.  Must include all available options.
            'option_combinations': feedback_report_combinations,
                          # A function that returns a list of dicts of option
                          # values that covers all the combinations (assuming
                          # you want to pre-cache these combinations. If there
                          # are no options, just use None.
            'generate': feedback_report
                          # The report function. Should return the data as a
                          # JSON-ifyable object.
        }
        """
