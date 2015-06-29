from ckanext.report.report_registry import ReportRegistry
from ckan.plugins import toolkit as tk
import ckan.lib.helpers
from ckan import model


def relative_url_for(**kwargs):
    '''Return the existing URL but amended for the given url_for-style
    parameters. Much easier than calling h.add_url_param etc. For switching to
    URLs inside the current controller action only.
    '''
    # Restrict the request params to the same action & controller, to avoid
    # being an open redirect.
    disallowed_params = set(('controller', 'action', 'anchor', 'host',
                             'protocol', 'qualified'))
    user_specified_params = [(k, v) for k, v in tk.request.params.items()
                             if k not in disallowed_params]
    args = dict(tk.request.environ['pylons.routes_dict'].items()
                + user_specified_params
                + kwargs.items())
    # remove blanks
    for k, v in args.items():
        if not v:
            del args[k]
    return tk.url_for(**args)


def chunks(list_, size):
    '''Splits up a given list into 'size' sized chunks.'''
    for i in xrange(0, len(list_), size):
        yield list_[i:i+size]


def organization_list():
    organizations = model.Session.query(model.Group).\
        filter(model.Group.type=='organization').\
        filter(model.Group.state=='active').order_by('title')
    for organization in organizations:
        yield (organization.name, organization.title)


def render_datetime(datetime_, date_format=None, with_hours=False):
    '''Render a datetime object or timestamp string as a pretty string
    (Y-m-d H:m).
    If timestamp is badly formatted, then a blank string is returned.

    This is a wrapper on the CKAN one which has an American date_format.
    '''
    if not date_format:
        date_format = '%d %b %Y'
    if with_hours:
        date_format += ' %H:%M'
    return ckan.lib.helpers.render_datetime(datetime_, date_format)


def explicit_default_options(report_name):
    '''Returns the options that are needed for URL parameters to load a report
    with the default options.

    Normally you can just load a report at /report/<name> but there is an
    exception for checkboxes that default to True. e.g.
    include_sub_organizations.  If you uncheck the checkbox and submit the form
    then rather than sending you to /report/<name>?include_sub_organizations=0
    it misses out the parameter completely. Therefore the absence of the
    parameter must be taken to mean include_sub_organizations=0, and when we
    want the (default) value of 1 we have to be explicit.
    '''
    explicit_defaults = {}
    options = ReportRegistry.instance().get_report(report_name).option_defaults
    for key in options:
        if options[key] is True:
            explicit_defaults[key] = 1
    return explicit_defaults
