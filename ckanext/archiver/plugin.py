import logging
from datetime import datetime
import json
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

        log.debug('Notified of resource event: %s', entity.id)

        if operation:
            # Only interested in 'new resource' events, since that's what you
            # get when you change the URL field. Note that once this occurs, in tasks.py
            # it will update the resource with the new cache_url, that will cause a 
            # 'change resource' notification, which we need to ignore here.
            if operation == model.DomainObjectOperation.new:
                self._create_archiver_task(entity)
            else:
                log.debug('Ignoring resource event because operation is: %s',
                          operation)
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            self._create_archiver_task(entity)

    def _create_archiver_task(self, resource):
        from ckan.lib.base import c
        site_user = get_action('get_site_user')(
            {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )
        # If the code that triggers this is run from the command line, the c 
        # stacked object proxy variable will not have been set up by the paste
        # registry so will give an error saying no object has been registered
        # for this thread. The easiest thing to do is to catch this, but it 
        # would be nice to have a config option so that the behaviour can be 
        # specified.
        try:
            c.user
        except TypeError:
            # This is no different from running the archiver from the command line:
            # See https://github.com/okfn/ckanext-archiver/blob/master/ckanext/archiver/commands.py
            username = site_user['name']
            userapikey = site_user['apikey']
        else:
            user = model.User.by_name(c.user)
            username = user.name
            userapikey = user.apikey
        context = json.dumps({
            'site_url': self.site_url,
            'apikey': userapikey,
            'username': username,
            'cache_url_root': self.cache_url_root,
            'site_user_apikey': site_user['apikey']
        })
        res_dict = resource_dictize(resource, {'model': model})
        data = json.dumps(res_dict)

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
            'user': site_user['name'],
            'ignore_auth': True
        }

        get_action('task_status_update')(archiver_task_context, archiver_task_status)
        celery.send_task("archiver.update", args=[context, data], task_id=task_id)
        log.debug('Archival of resource put into celery queue: %s url=%r user=%s site_user=%s site_url=%s', resource.id, res_dict.get('url'), username, site_user['name'], self.site_url)
