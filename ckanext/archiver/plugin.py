from ckan import model
from ckan.plugins import SingletonPlugin, implements, IDomainObjectModification, IResourceUrlChange
from celery.execute import send_task

class ArchiverPlugin(SingletonPlugin):
    """
    Registers to be notified whenever CKAN resources are created or their URLs change,
    and will create a new ckanext.archiver celery task to archive the resource.
    """
    implements(IDomainObjectModification, inherit=True)
    implements(IResourceUrlChange)

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Resource):
            return

        if operation:
            if operation == model.DomainObjectOperation.new:
                send_task("archiver.update", [entity.id])
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            send_task("archiver.update", [entity.id])

