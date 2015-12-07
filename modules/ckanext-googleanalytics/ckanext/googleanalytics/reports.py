'''
Working examples - simple tag report.
'''

from ckanext.
from ckan.lib.helpers import OrderedDict
from ckanext.googleanalytics.model import PackageStats,ResourceStats


def google_analytics_report(last):
    '''
    Generates report based on google analytics data. number of views and downloads per resource and package
    '''
    # get package objects corresponding to popular GA content
    top_packages = PackageStats.get_top_packages(limit=last)
    top_resources = ResourceStats.get_top_resources(limit=last)

    return {
        'top_packages': top_packages,
        'top_resources': top_resources
        }


googleanalytics_report_info = {
    'name': 'google-analytics',
    'description': 'Analytics showing resource views',
    'option_defaults': OrderedDict((('last',20)),
    'option_combinations': None,
    'generate': google_analytics_report,
    'template': 'report/analytics.html',
    }
