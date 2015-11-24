import logging

from ckan import model
from ckan import plugins as p

from ckanext.report.interfaces import IReport
from ckanext.archiver.interfaces import IPipe
from ckanext.archiver.logic import action, auth
from ckanext.archiver import helpers
from ckanext.archiver import lib
from ckanext.archiver.model import Archival, aggregate_archivals_for_a_dataset

log = logging.getLogger(__name__)


class ArchiverPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    """
    Registers to be notified whenever CKAN resources are created or their URLs
    change, and will create a new ckanext.archiver celery task to archive the
    resource.
    """
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(IReport)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)

    # IDomainObjectModification

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Package):
            return

        log.debug('Notified of package event: %s %s', entity.id, operation)

        lib.create_archiver_package_task(entity, 'priority')

    # IReport

    def register_reports(self):
        """Register details of an extension's reports"""
        from ckanext.archiver import reports
        return [reports.broken_links_report_info,
                ]

    # IConfigurer

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')

    # IActions

    def get_actions(self):
        return dict((name, function) for name, function
                    in action.__dict__.items()
                    if callable(function))

    # IAuthFunctions

    def get_auth_functions(self):
        return dict((name, function) for name, function
                    in auth.__dict__.items()
                    if callable(function))

    # ITemplateHelpers

    def get_helpers(self):
        return dict((name, function) for name, function
                    in helpers.__dict__.items()
                    if callable(function) and name[0] != '_')

    # IPackageController

    def after_show(self, context, pkg_dict):
        # Insert the archival info into the package_dict so that it is
        # available on the API.
        # When you edit the dataset, these values will not show in the form,
        # it they will be saved in the resources (not the dataset). I can't see
        # and easy way to stop this, but I think it is harmless. It will get
        # overwritten here when output again.
        archivals = Archival.get_for_package(pkg_dict['id'])
        if not archivals:
            return
        # dataset
        dataset_archival = aggregate_archivals_for_a_dataset(archivals)
        pkg_dict['archiver'] = dataset_archival
        # resources
        archivals_by_res_id = dict((a.resource_id, a) for a in archivals)
        for res in pkg_dict['resources']:
            archival = archivals_by_res_id.get(res['id'])
            if archival:
                archival_dict = archival.as_dict()
                del archival_dict['id']
                del archival_dict['package_id']
                del archival_dict['resource_id']
                res['archiver'] = archival_dict


class TestIPipePlugin(p.SingletonPlugin):
    """
    """
    p.implements(IPipe, inherit=True)

    def __init__(self, *args, **kwargs):
        self.calls = []

    def reset(self):
        self.calls = []

    def receive_data(self, operation, queue, **params):
        self.calls.append([operation, queue, params])
