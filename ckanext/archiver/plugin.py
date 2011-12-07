from datetime import datetime
import json
from ckan import model
from ckan.model.types import make_uuid
from ckan.plugins import SingletonPlugin, implements, IDomainObjectModification, \
    IResourceUrlChange, IConfigurable
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.logic import get_action
from ckan.lib.celery_app import celery

class ArchiverPlugin(SingletonPlugin):
    """
    Registers to be notified whenever CKAN resources are created or their URLs change,
    and will create a new ckanext.archiver celery task to archive the resource.
    """
    implements(IDomainObjectModification, inherit=True)
    implements(IResourceUrlChange)
    implements(IConfigurable)

    def configure(self, config):
        self.site_url = config.get('ckan.site_url')
        self.cache_url_root = config.get('ckan.cache_url_root')

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Resource):
            return
        
        if operation:
            if operation == model.DomainObjectOperation.new:
                self._create_archiver_task(entity)
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            self._create_archiver_task(entity)

    def _create_archiver_task(self, resource):
        user = get_action('get_site_user')({'model': model,
                                            'ignore_auth': True,
                                            'defer_commit': True}, {})
        context = json.dumps({
            'site_url': self.site_url,
            'apikey': user.get('apikey'),
            'username': user.get('name'),
            'cache_url_root': self.cache_url_root
        })
        data = json.dumps(resource_dictize(resource, {'model': model}))

        task_id = make_uuid()
        archiver_task_status = {
            'entity_id': resource.id,
            'entity_type': u'resource',
            'task_type': u'archiver',
            'key': u'celery_task_id',
            'value': task_id,
            'error': u'',
            'last_updated': datetime.now().isoformat()
        }
        archiver_task_context = {
            'model': model, 
            'user': user.get('name'),
        }
        
        get_action('task_status_update')(archiver_task_context, archiver_task_status)
        celery.send_task("archiver.update", args=[context, data], task_id=task_id)

