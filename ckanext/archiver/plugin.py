import os
import logging

from ckan import model
from ckan.model.types import make_uuid
from ckan import plugins as p
from ckan.lib.celery_app import celery

from ckanext.report.interfaces import IReport
from ckanext.archiver.interfaces import IPipe
from ckanext.archiver.logic import action, auth
from ckanext.archiver import helpers
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
    #p.implements(p.IDatasetForm, inherit=True)

    # IDomainObjectModification

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Package):
            return

        log.debug('Notified of package event: %s %s', entity.id, operation)

        create_archiver_package_task(entity, 'priority')

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

    # IDatasetForm

    def package_types(self):
        return ['dataset']

    def is_fallback(self):
        # This is just a fallback, so a site-specific extension can have their
        # own IDatasetForm for datasets, but they they will lose the ability to
        # see broken-link info on the dataset and in the API, unless they
        # integrate the following schema changes in this IDataset form into
        # their one.
        return True

    def update_package_schema(self):
        schema = p.toolkit.DefaultDatasetForm.update_package_schema(self)
        # don't save archiver info in the dataset, since it is stored in the
        # archival table instead, and the value added into the package_show
        # result in the show_package_schema
        ignore = p.toolkit.get_validator('ignore')
        schema['archiver'] = [ignore]
        schema['resources']['archiver'] = [ignore]
        return schema

    def show_package_schema(self):
        schema = p.toolkit.DefaultDatasetForm.show_package_schema(self)
        schema['archiver'] = [add_archival_information]
        return schema


# this is a validator/converter
def add_archival_information(key, data, errors, context):
    archivals = Archival.get_for_package(data[('id',)])
    # dataset
    dataset_archival = aggregate_archivals_for_a_dataset(archivals)
    data[key] = dataset_archival
    # resources
    # (insert archival info into resources here, rather than in a separate
    # per-resource validator, because that would mean getting the archival info
    # from the database again separately for each resource)
    archivals_by_res_id = dict((a.resource_id, a) for a in archivals)
    res_index = 0
    while True:
        res_id_key = ('resources', res_index, u'id')
        if res_id_key not in data:
            # no more resources
            break
        res_id = data[res_id_key]
        archival = archivals_by_res_id.get(res_id)
        if archival:
            archival_dict = archival.as_dict()
            del archival_dict['id']
            del archival_dict['package_id']
            del archival_dict['resource_id']
            data[('resources', res_index, key[0])] = archival_dict
        res_index += 1


def create_archiver_resource_task(resource, queue):
    from pylons import config
    if hasattr(model, 'ResourceGroup'):
        # earlier CKANs had ResourceGroup
        package = resource.resource_group.package
    else:
        package = resource.package
    task_id = '%s/%s/%s' % (package.name, resource.id[:4], make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config['__file__'])
    celery.send_task('archiver.update_resource', args=[ckan_ini_filepath, resource.id, queue],
                     task_id=task_id, queue=queue)
    log.debug('Archival of resource put into celery queue %s: %s/%s url=%r', queue, package.name, resource.id, resource.url)

def create_archiver_package_task(package, queue):
    from pylons import config
    task_id = '%s/%s' % (package.name, make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config['__file__'])
    celery.send_task('archiver.update_package', args=[ckan_ini_filepath, package.id, queue],
                     task_id=task_id, queue=queue)
    log.debug('Archival of package put into celery queue %s: %s', queue, package.name)


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
