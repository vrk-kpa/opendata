from pylons import config

from ckan import model
from ckan.common import request, c, _
from ckan.logic import get_action, NotFound, NotAuthorized, check_access, clean_dict, tuplize_dict, parse_params, ValidationError
import ckan.lib.navl.dictization_functions as dictization_functions
from ckan.lib import helpers as h
from ckan.controllers.user import UserController
from ckan.lib.base import abort, validate, render
import ckan.new_authz as authz


import logging

log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
DataError = dictization_functions.DataError


class YtpUserController(UserController):

    # Modify original CKAN Edit user controller
    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'keep_apikey': True, 'keep_email': True
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        try:
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to edit a user.'))

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = validate(old_data, schema)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (authz.is_sysadmin(c.user) or c.user == user_obj.name):
            abort(401, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user or c.author},
                                       data_dict)

        c.is_myself = True
        c.show_email_notifications = h.asbool(
            config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='user', action='edit',
                      id=user_ref)

    def read(self, id=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj}

        context['with_related'] = True

        self._setup_template_variables(context, data_dict)

        c.user_dict['datasets'] = []

        # find datasets for requested id

        userobj = model.User.get(c.user_dict['id'])

        user_dataset_q = (model.Session.query(model.Package)
                          .join(model.PackageRole)
                          .filter_by(user=userobj, role=model.Role.ADMIN)
                          .order_by(None))

        # if signed in, find datasets for organizations where user is admin
        if c.userobj and c.userobj.name == id:
                orgs = h.organizations_available('admin')
                org_ids = []
                for org in orgs:
                    org_ids.append(org['id'])
                if len(org_ids):
                    org_dataset_q = (model.Session.query(model.Package)
                                     .join(model.PackageRole)
                                     .filter_by(role=model.Role.ADMIN)
                                     .filter(model.Package.owner_org.in_(org_ids))
                                     .join(model.User)
                                     .filter(model.User.name != 'harvest')
                                     .filter(model.User.name != 'default')
                                     .order_by(None))

                    dataset_q = user_dataset_q.union(org_dataset_q)
                else:
                    dataset_q = user_dataset_q
        else:
            dataset_q = user_dataset_q

        # get datasets, access rights are checked during package_show
        for dataset in dataset_q:
            try:
                dataset_dict = get_action('package_show')(
                    context, {'id': dataset.id})
            except NotAuthorized:
                continue
            c.user_dict['datasets'].append(dataset_dict)

        # The legacy templates have the user's activity stream on the user
        # profile page, new templates do not.
        if h.asbool(config.get('ckan.legacy_templates', False)):
            c.user_activity_stream = get_action('user_activity_list_html')(
                context, {'id': c.user_dict['id']})

        return render('user/read.html')

    def _save_edit(self, id, context):
        try:
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id

            # MOAN: Do I really have to do this here?
            if 'activity_streams_email_notifications' not in data_dict:
                data_dict['activity_streams_email_notifications'] = False

            get_action('user_update')(context, data_dict)
            h.flash_success(_('Profile updated'))
            h.redirect_to('home')
        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % id)
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)
