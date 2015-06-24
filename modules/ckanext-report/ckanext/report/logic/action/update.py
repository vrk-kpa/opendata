from ckanext.report.report_registry import ReportRegistry

import ckan.logic as logic

def report_refresh(context=None, data_dict=None):
    """
    Causes the cached data of the report to be refreshed

    :param id: The name of the report
    :type id: string

    :param options: Dictionary of options to pass to the report
    :type options: dict
    """
    logic.check_access('report_refresh', context, data_dict)

    id = logic.get_or_bust(data_dict, 'id')
    options = data_dict.get('options')

    report = ReportRegistry.instance().get_report(id)

    report.refresh_cache(options)
