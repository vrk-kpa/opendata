import ckan.plugins as p
from ckanext.report.interfaces import IReport

class YtpReportPlugin(p.SingletonPlugin):
    p.implements(IReport)
    p.implements(p.IConfigurer, inherit=True)

    # IReport

    def register_reports(self):
        import reports
        return [reports.test_report_info, reports.administrative_branch_summary_report_info]

    def update_config(self, config):
        from ckan.plugins import toolkit
        toolkit.add_template_directory(config, 'templates')
