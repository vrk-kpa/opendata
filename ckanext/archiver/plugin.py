import logging
import os

from ckan import model
from ckan.model.types import make_uuid
from ckan import plugins as p
from ckan.lib.celery_app import celery
from ckanext.report.interfaces import IReport
from ckanext.archiver.interfaces import IPipe

log = logging.getLogger(__name__)


class ArchiverPlugin(p.SingletonPlugin):
    """
    Registers to be notified whenever CKAN resources are created or their URLs
    change, and will create a new ckanext.archiver celery task to archive the
    resource.
    """
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(IReport)
    p.implements(p.IConfigurer, inherit=True)

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

def create_archiver_resource_task(resource, queue):
    from pylons import config
    package = resource.resource_group.package
    task_id = '%s/%s/%s' % (package.name, resource.id[:4], make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config.__file__)
    celery.send_task('archiver.update_resource', args=[ckan_ini_filepath, resource.id, queue],
                     task_id=task_id, queue=queue)
    log.debug('Archival of resource put into celery queue %s: %s/%s url=%r', queue, package.name, resource.id, resource.url)

def create_archiver_package_task(package, queue):
    from pylons import config
    task_id = '%s/%s' % (package.name, make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config.__file__)
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
