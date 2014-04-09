import logging
from datetime import datetime
import json
import os

from ckan import model
from ckan.model.types import make_uuid
from ckan.plugins import SingletonPlugin, implements, IDomainObjectModification, \
    IResourceUrlChange, IConfigurable
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.logic import get_action
from ckan.lib.celery_app import celery

log = logging.getLogger(__name__)

class ArchiverPlugin(SingletonPlugin):
    """
    Registers to be notified whenever CKAN resources are created or their URLs change,
    and will create a new ckanext.archiver celery task to archive the resource.
    """
    implements(IDomainObjectModification, inherit=True)
    implements(IResourceUrlChange)
    implements(IConfigurable)

    def configure(self, config):
        self.site_url = config.get('ckan.site_url_internally') or config.get('ckan.site_url')
        self.cache_url_root = config.get('ckan.cache_url_root')

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Resource):
            return

        log.debug('Notified of resource event: %s %s', entity.id, operation)

        if operation:
            # Only interested in 'new resource' events. Note that once this occurs,
            # in tasks.py it will update the resource with the new cache_url,
            # that will cause a 'change resource' notification, which we nee
            # to ignore here.
            if operation == model.DomainObjectOperation.new:
                create_archiver_task(entity, 'priority')
            else:
                log.debug('Ignoring resource event because operation is: %s',
                          operation)
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            create_archiver_task(entity, 'priority')


def create_archiver_task(resource, queue):
    from pylons import config
    package = resource.resource_group.package
    task_id = '%s/%s/%s' % (package.name, resource.id[:4], make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config.__file__)
    celery.send_task('archiver.update', args=[ckan_ini_filepath, resource.id],
                     task_id=task_id, queue=queue)
    log.debug('Archival of resource put into celery queue %s: %s/%s url=%r', queue, package.name, resource.id, resource.url)
