from ckan.lib.helpers import OrderedDict
from ckanext.googleanalytics.model import PackageStats,ResourceStats


def google_analytics_dataset_report(last):
    '''
    Generates report based on google analytics data. number of views per package
    '''
    # get package objects corresponding to popular GA content
    top_packages = PackageStats.get_top(limit=last)

    return {
        'table' : top_packages.get("packages")
    }

def google_analytics_dataset_option_combinations():
    options = [20,25,30,35,40,45,50]
    for option in options:
        yield { 'last': option }

googleanalytics_dataset_report_info = {
    'name': 'google-analytics-dataset',
    'title': 'Popular datasets',
    'description': 'Google analytics showing top datasets with most views',
    'option_defaults': OrderedDict((('last',20),)),
    'option_combinations': google_analytics_dataset_option_combinations,
    'generate': google_analytics_dataset_report,
    'template': 'report/dataset_analytics.html',
    }


def google_analytics_resource_report(last):
    '''
    Generates report based on google analytics data. number of views per package
    '''
    # get resource objects corresponding to popular GA content
    top_resources = ResourceStats.get_top(limit=last)

    return {
        'table' : top_resources.get("resources")
    }

def google_analytics_resource_option_combinations():
    options = [20,25,30,35,40,45,50]
    for option in options:
        yield { 'last': option }

googleanalytics_resource_report_info = {
    'name': 'google-analytics-resource',
    'title': 'Popular resources',
    'description': 'Google analytics showing most downloaded resources',
    'option_defaults': OrderedDict((('last',20),)),
    'option_combinations': google_analytics_resource_option_combinations,
    'generate': google_analytics_resource_report,
    'template': 'report/resource_analytics.html'
}

