from ckan.logic import NotAuthorized
from ckan.lib.base import abort
from ckan.controllers.user import UserController
from ckan.plugins.core import get_plugin
from ckan.common import _
from pylons.controllers.util import redirect
from ckan.common import c, request
import uuid
from ckan.plugins import toolkit
from ckan import model
from ckan.lib.base import render


class YtpDrupalController(UserController):
    def delete_me(self):
        try:
            if not c.userobj:
                raise NotAuthorized

            if request.params.get('delete', None) != 'true':
                return render('user/delete_me.html')

            from ckan.lib.celery_app import celery
            context = {'model': model, 'session': model.Session, 'user': c.user}
            toolkit.check_access('user_delete_me', context, {})

            celery.send_task("ckanext.ytp_drupal.delete_user", args=(c.userobj.id,), task_id=str(uuid.uuid4()))
            redirect(get_plugin('ytp_drupal').cancel_url)
        except NotAuthorized:
            msg = _('Unauthorized to delete user')
            abort(401, msg.format(user_id=id))
