from ckan import model
from ckan.common import c, _
from ckan.logic import get_action, NotFound, NotAuthorized
from ckan.controllers.organization import OrganizationController
from ckan.lib.base import abort

import logging

log = logging.getLogger(__name__)


class YtpOrganizationController(OrganizationController):
    def members(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        try:
            c.members = self._action('member_list')(
                context, {'id': id, 'object_type': 'user'}
            )
            c.group_dict = self._action('group_show')(context, {'id': id})

            members = []
            for user_id, name, role in c.members:

                user_context = {
                    'model': model, 'session': model.Session,
                    'user': user_id, 'auth_user_obj': c.userobj,
                    'keep_email': True
                }
                user_dict = {'id': user_id}
                data = get_action('user_show')(user_context, user_dict)
                members.append((user_id, name, role, data['email']))

            c.members = members
        except NotAuthorized:
            abort(401, _('Unauthorized to delete group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        return self._render_template('group/members.html')
