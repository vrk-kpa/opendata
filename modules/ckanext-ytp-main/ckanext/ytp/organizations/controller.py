from ckan import model
from ckan.common import c, _, request
from ckan.logic import get_action, NotFound, NotAuthorized
from ckan.controllers.organization import OrganizationController
from ckan.lib.base import abort, render
from ckan.logic import check_access
import ckan.lib.helpers as h

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

            check_access('group_update', context, {'id': id})
            context['keep_email'] = True
            context['auth_user_obj'] = c.userobj
            context['return_minimal'] = True

            members = []
            for user_id, name, role in c.members:
                user_dict = {'id': user_id}
                data = get_action('user_show')(context, user_dict)
                if data['state'] != 'deleted':
                    members.append((user_id, data['name'], role, data['email']))

            c.members = members
        except NotAuthorized:
            abort(401, _('Unauthorized to view group %s members') % id)
        except NotFound:
            abort(404, _('Group not found'))
        return self._render_template('group/members.html')

    def user_list(self):
        if c.userobj and c.userobj.sysadmin:

            q = model.Session.query(model.Group, model.Member, model.User). \
                filter(model.Member.group_id == model.Group.id). \
                filter(model.Member.table_id == model.User.id). \
                filter(model.Member.table_name == 'user'). \
                filter(model.User.name != 'harvest'). \
                filter(model.User.name != 'default'). \
                filter(model.User.state == 'active')

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

    def admin_list(self):
        if c.userobj and c.userobj.sysadmin:

            q = model.Session.query(model.Group, model.Member, model.User). \
                filter(model.Member.group_id == model.Group.id). \
                filter(model.Member.table_id == model.User.id). \
                filter(model.Member.table_name == 'user'). \
                filter(model.Member.capacity == 'admin'). \
                filter(model.User.name != 'harvest'). \
                filter(model.User.name != 'default'). \
                filter(model.User.state == 'active')

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

        return self._render_template('group/admin_list.html')

    def read(self, id, limit=20):
        try:
            context = {
                'model': model,
                'session': model.Session,
                'user': c.user or c.author
            }
            check_access('group_show', context, {'id': id})
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            g = model.Session.query(model.Group).filter(model.Group.name == id).first()
            if g is None or g.state != 'active':
                return self._render_template('group/organization_not_found.html')

        return OrganizationController.read(self, id, limit)

    def embed(self, id, limit=5):
        """
            Fetch given organization's packages and show them in an embeddable list view.
            See Nginx config for X-Frame-Options SAMEORIGIN header modifications.
        """

        def make_pager_url(q=None, page=None):
            ctrlr = 'ckanext.ytp.organizations.controller:YtpOrganizationController'
            url = h.url_for(controller=ctrlr, action='embed', id=id)
            return url + u'?page=' + str(page)

        try:
            context = {
                'model': model,
                'session': model.Session,
                'user': c.user or c.author
            }
            check_access('group_show', context, {'id': id})
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            g = model.Session.query(model.Group).filter(model.Group.name == id).first()
            if g is None or g.state != 'active':
                return self._render_template('group/organization_not_found.html')

        page = OrganizationController._get_page_number(self, request.params)

        group_dict = {'id': id}
        group_dict['include_datasets'] = False
        c.group_dict = self._action('group_show')(context, group_dict)
        c.group = context['group']

        q = c.q = request.params.get('q', '')
        q += ' owner_org:"%s"' % c.group_dict.get('id')

        data_dict = {
            'q': q,
            'rows': limit,
            'start': (page - 1) * limit,
            'extras': {}
        }

        query = get_action('package_search')(context, data_dict)

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=make_pager_url,
            item_count=query['count'],
            items_per_page=limit
        )

        c.page.items = query['results']

        return render("organization/embed.html")
