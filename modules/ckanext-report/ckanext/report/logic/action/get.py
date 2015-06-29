from ckanext.report.report_registry import ReportRegistry
import ckan.plugins as p
import ckan.logic as logic


@logic.side_effect_free
def report_list(context=None, data_dict=None):
    """
    Lists all available reports

    :returns: A list of report dictionaries (see report_show)
    :rtype: list
    """
    logic.check_access('report_list', context, data_dict)

    registry = ReportRegistry.instance()
    reports = registry.get_reports()

    user = context['auth_user_obj']
    reports = filter(lambda r: r.is_visible_to_user(user), reports)

    return [report.as_dict() for report in reports]


@logic.side_effect_free
def report_show(context=None, data_dict=None):
    """
    Shows a single report

    Does not provide the data for the report which must be obtained by a
    separate call to report_data_get.

    :param id: The name of the report
    :type id: string

    :returns: A dictionary of information about the report
    :rtype: dictionary
    """
    logic.check_access('report_show', context, data_dict)

    id = logic.get_or_bust(data_dict, 'id')

    try:
        report = ReportRegistry.instance().get_report(id)
    except KeyError:
        raise p.toolkit.ObjectNotFound('Report not found: %s' % id)

    return report.as_dict()


@logic.side_effect_free
def report_data_get(context=None, data_dict=None):
    """
    Returns the data for the report

    The data may have been cached in the database or may have been generated on
    demand so the date when the data was generated is also returned

    :param id: The name of the report
    :type id: string

    :param options: Dictionary of options to pass to the report (optional)
    :type options: dict

    :returns: A list containing the data and the date on which it was created
    :rtype: list
    """
    logic.check_access('report_data_get', context, data_dict)

    id = logic.get_or_bust(data_dict, 'id')
    options = data_dict.get('options', {})

    report = ReportRegistry.instance().get_report(id)

    data, date = report.get_fresh_report(**options)

    return data, date.isoformat()


@logic.side_effect_free
def report_key_get(context=None, data_dict=None):
    """
    Returns a key that will identify the report and options

    :param id: The name of the report
    :type id: string

    :param options: Dictionary of options to pass to the report
    :type options: dict

    :returns: A key to identify the report
    :rtype: string
    """
    logic.check_access('report_key_get', context, data_dict)

    id = logic.get_or_bust(data_dict, 'id')
    options = data_dict.get('options')

    report = ReportRegistry.instance().get_report(id)

    return report.generate_key(options).replace('?', '_')
