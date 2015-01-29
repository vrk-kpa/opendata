from ckan import model
from ckan.common import c, _
from ckan.logic import get_action, NotFound, NotAuthorized
from ckan.controllers.organization import OrganizationController
from ckan.lib.base import abort
from ckan.lib.dictization.model_dictize import user_dictize, group_dictize, group_list_dictize
from ckan.new_authz import get_roles_with_permission

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
                members.append((user_id, data['name'], role, data['email']))

            c.members = members
        except NotAuthorized:
            abort(401, _('Unauthorized to delete group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        return self._render_template('group/members.html')

    def user_list(self):
        if c.userobj and c.userobj.sysadmin:

            q = model.Session.query(model.Group, model.Member, model.User). \
                filter(model.Member.group_id == model.Group.id). \
                filter(model.Member.table_id == model.User.id). \
                filter(model.Member.table_name == 'user'). \
                filter(model.Group.id != 'yksityishenkilo'). \
                filter(model.User.name != 'harvest'). \
                filter(model.User.name != 'default')

            users = []

            for group, member, user in q.all():
                users.append({
                    'user_id': user.id,
                    'username': user.name,
                    'organization': group.title,
                    'role': member.capacity,
                    'email': user.email
                })


            c.users = users
        else:
            c.users = []

        return self._render_template('group/user_list.html')
