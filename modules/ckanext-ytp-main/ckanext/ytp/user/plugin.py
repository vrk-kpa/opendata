from ckan.plugins import toolkit
from ckanext.ytp.user import logic
from ckan import plugins, model
from webhelpers.html.tags import link_to, literal
from ckan.lib import helpers
from ckan.common import c
from ckan.config.routing import SubMapper
from pylons import config


def _get_user_image(user):
    image_url = user.extras.get('image_url', None)
    if not image_url:
        return helpers.url_for_static('images/user_placeholder_box.png')
    elif not image_url.startswith('http'):
        return helpers.url_for_static('uploads/user/%s' % image_url, qualified=True)
    return image_url


def _user_image(user, size):
    url = _get_user_image(user) or ""
    return literal('<img src="%s" width="%s" height="%s" class="media-image" />' % (url, size, size))


def helper_is_pseudo(user):
    """ Check if user is pseudo user """
    return user in [model.PSEUDO_USER__LOGGED_IN, model.PSEUDO_USER__VISITOR]


def helper_linked_user(user, maxlength=0, avatar=20):
    """ Return user as HTML item """
    if helper_is_pseudo(user):
        return user
    if not isinstance(user, model.User):
        user_name = unicode(user)
        user = model.User.get(user_name)
        if not user:
            return user_name
    if user:
        name = user.name if model.User.VALID_NAME.match(user.name) else user.id
        icon = _user_image(user, avatar)
        displayname = user.display_name
        if maxlength and len(user.display_name) > maxlength:
            displayname = displayname[:maxlength] + '...'
        return icon + u' ' + link_to(displayname,
                                     helpers.url_for(controller='user', action='read', id=name), class_='')


def helper_organizations_for_select():
    organizations = [{'value': organization['id'], 'text': organization['display_name']} for organization in helpers.organizations_available()]
    return [{'value': '', 'text': ''}] + organizations


def helper_main_organization(user=None):
    user = user or c.userobj

    if not user:
        return None

    main_organization = user.extras.get('main_organization', None)

    if main_organization:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        return toolkit.get_action('organization_show')(context, {'id': main_organization})
    else:
        if c.userobj.sysadmin:
            return None  # Admin is part of all organization so main organization would be invalid every time.
        available = helpers.organizations_available()
        return available[0] if available else None


def get_image_upload_size():
    return config.get('ckan.max_image_size', 2)


class YtpUserPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    default_domain = None

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('../common/public/javascript/', 'ytp_common_js')
        toolkit.add_public_directory(config, 'public')

    def configure(self, config):
        from ckanext.ytp.user.model import setup as model_setup
        model_setup()

    def get_helpers(self):
        return {'linked_user': helper_linked_user, 'organizations_for_select': helper_organizations_for_select, 'is_pseudo': helper_is_pseudo,
                'main_organization': helper_main_organization,
                'get_image_upload_size': get_image_upload_size}

    def get_auth_functions(self):
        return {'user_update': logic.auth_user_update, 'user_list': logic.auth_user_list, 'admin_list': logic.auth_admin_list}

    def get_actions(self):
        return {'user_update': logic.action_user_update, 'user_show': logic.action_user_show, 'user_list': logic.action_user_list}

    def before_map(self, map):
        # Remap user edit to our user controller
        user_controller = 'ckanext.ytp.user.controller:YtpUserController'
        with SubMapper(map, controller=user_controller) as m:
            m.connect('/user/edit', action='edit')
            m.connect('/user/edit/{id:.*}', action='edit')
            m.connect('/user/me', action='me')
            m.connect('/user/{id}', action='read')

        return map
