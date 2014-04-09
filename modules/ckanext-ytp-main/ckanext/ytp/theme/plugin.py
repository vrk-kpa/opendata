from ckan import plugins
from ckan.plugins import toolkit
from ckanext.ytp.theme import menu
import types
from ckan.common import c


class YtpThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)

    plugins.implements(plugins.IConfigurer)

    default_domain = None

    # TODO: We should use named routes instead
    _manu_map = [(['/user/%(username)s', '/%(language)s/user/%(username)s'], menu.UserMenu, menu.MyInformationMenu),
                 (['/dashboard/organizations', '/%(language)s/dashboard/organizations'], menu.UserMenu, menu.MyOrganizationMenu),
                 (['/dashboard/datasets', '/%(language)s/dashboard/datasets'], menu.UserMenu, menu.MyDatasetsMenu),
                 (['/user/delete-me', '/%(language)s/user/delete-me'], menu.UserMenu, menu.MyCancelMenu),
                 (['/user/edit', '/%(language)s/user/edit', '/user/edit/%(username)s', '/%(language)s/user/edit/%(username)s'],
                  menu.UserMenu, menu.MyPersonalDataMenu),
                 (['/user', '/%(language)s/user'], menu.ProducersMenu, menu.ListUsersMenu),
                 (['/%(language)s/organization', '/organization'], menu.ProducersMenu, menu.OrganizationMenu)]

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, '/var/www/resources/templates')
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/css/', 'ytp_css')
        toolkit.add_resource('/var/www/resources', 'ytp_resources')
        toolkit.add_resource('public/js/', 'ytp_js')

    def configure(self, config):
        self.default_domain = config.get("ckanext.ytp.theme.default_domain")

    def _short_domain(self, hostname, default=None):
        if not hostname or hostname[0].isdigit():
            return default or self.default_domain or ""
        return '.'.join(hostname.split('.')[-2:])

    def _get_menu_tree(self, current_url, language):
        for patterns, handler, selected in self._manu_map:
            for pattern in patterns:
                if type(pattern) in types.StringTypes:
                    values = {'language': language}
                    if c.user:
                        values['username'] = c.user
                    try:
                        url = pattern % values
                        if current_url.split("?", 1)[0] == url:
                            return handler(self).select(selected).to_drupal_dictionary()
                    except KeyError:
                        pass  # user not logged in
                elif pattern.match(current_url):
                    return handler(self).select(selected).to_drupal_dictionary()
        return None

    def _get_menu_for_page(self, current_url, language):
        """ Fetches static side menu for url and language. """
        tree = self._get_menu_tree(current_url, language)
        if tree:
            return {'tree': tree}
        else:
            return {}

    def get_helpers(self):
        return {'short_domain': self._short_domain, 'get_menu_for_page': self._get_menu_for_page}
