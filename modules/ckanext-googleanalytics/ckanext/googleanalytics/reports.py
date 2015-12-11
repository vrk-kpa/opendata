from ckan.lib.helpers import OrderedDict
from ckanext.googleanalytics.model import PackageStats,ResourceStats


def google_analytics_report(last):
    '''
    Generates report based on google analytics data. number of views and downloads per resource and package
    '''
    # get package objects corresponding to popular GA content
    top_packages = PackageStats.get_top(limit=last)
    top_resources = ResourceStats.get_top(limit=last)

    return {
        'table' : top_packages 
    }

def google_analytics_option_combinations():
    options = [10,15,20,25,30,35,40,45,50]
    for option in options:
        yield { 'last': option }

googleanalytics_report_info = {
    'name': 'google-analytics',
    'description': 'Analytics showing resource views',
    'option_defaults': OrderedDict((('last',20),)),
    'option_combinations': google_analytics_option_combinations,
    'generate': google_analytics_report,
    'template': 'report/analytics.html',
    }
