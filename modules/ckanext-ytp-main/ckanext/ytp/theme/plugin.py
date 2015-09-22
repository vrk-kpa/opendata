from ckan import plugins
from ckan.plugins import toolkit
from ckan.common import c
from ckanext.ytp.theme import menu
import types
import urlparse
from webhelpers.html.builder import literal
import re
from ckan.lib import helpers


class YtpThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)

    default_domain = None
    logos = {}

    # TODO: We should use named routes instead
    _manu_map = [(['/user/%(username)s', '/%(language)s/user/%(username)s'], menu.UserMenu, menu.MyInformationMenu),
                 (['/dashboard/organizations', '/%(language)s/dashboard/organizations'], menu.UserMenu, menu.MyOrganizationMenu),
                 (['/dashboard/datasets', '/%(language)s/dashboard/datasets'], menu.UserMenu, menu.MyDatasetsMenu),
                 (['/user/delete-me', '/%(language)s/user/delete-me'], menu.UserMenu, menu.MyCancelMenu),
                 (['/user/edit', '/%(language)s/user/edit', '/user/edit/%(username)s', '/%(language)s/user/edit/%(username)s'],
                  menu.UserMenu, menu.MyPersonalDataMenu),
                 (['/user/activity/%(username)s', '/%(language)s/user/activity/%(username)s'], menu.UserMenu, menu.MyInformationMenu),
                 (['/user', '/%(language)s/user'], menu.ProducersMenu, menu.ListUsersMenu),
                 (['/%(language)s/organization', '/organization'], menu.ProducersMenu, menu.OrganizationMenu),
                 (['/%(language)s/dataset/new?collection_type=Open+Data', '/dataset/new?collection_type=Open+Data'], menu.PublishMenu, menu.PublishDataMenu),
                 (['/%(language)s/dataset/new?collection_type=Interoperability+Tools', '/dataset/new?collection_type=Interoperability+Tools'],
                  menu.PublishMenu, menu.PublishToolsMenu),
                 (['/%(language)s/service/new', '/service/new'],
                  menu.PublishMenu, menu.PublishServiceMenu),
                 (['/%(language)s/postit/return', '/postit/return'], menu.ProducersMenu, menu.PostitNewMenu),
                 (['/%(language)s/postit/new', '/postit/new'], menu.ProducersMenu, menu.PostitNewMenu)]

    # IRoutes #

    def before_map(self, m):
        """ Redirect data-path in stand-alone environment directly to CKAN. """
        m.redirect('/data/*(url)', '/{url}', _redirect_code='301 Moved Permanently')
        return m

    # IConfigurer #

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, '/var/www/resources/templates')
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/css/', 'ytp_css')
        toolkit.add_resource('/var/www/resources', 'ytp_resources')

    # IConfigurable #

    def configure(self, config):
        self.default_domain = config.get("ckanext.ytp.theme.default_domain")
        logos = config.get("ckanext.ytp.theme.logos")
        if logos:
            self.logos = dict(item.split(":") for item in re.split("\s+", logos.strip()))

    # ITemplateHelpers #

    def _short_domain(self, hostname, default=None):
        if not hostname or hostname[0].isdigit():
            return default or self.default_domain or ""
        return '.'.join(hostname.split('.')[-2:])

    def _get_menu_tree(self, current_url, language):
        parsed_url = urlparse.urlparse(current_url)
        for patterns, handler, selected in self._manu_map:
            for pattern in patterns:
                if type(pattern) in types.StringTypes:
                    values = {'language': language}
                    if c.user:
                        values['username'] = c.user
                    try:
                        pattern_url = urlparse.urlparse(pattern % values)

                        if parsed_url.path == pattern_url.path:
                            skip = False
                            if pattern_url.query:
                                parsed_parameters = urlparse.parse_qs(parsed_url.query)
                                if not parsed_parameters:
                                    skip = True
                                else:
                                    for key, value in urlparse.parse_qs(pattern_url.query).iteritems():
                                        parameter = parsed_parameters.get(key, None)
                                        if not parameter or parameter[0] != value[0]:
                                            skip = True
                                            break
                            if not skip:
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

    def _site_logo(self, hostname, default=None):

        if "avoindata" in hostname:
            hostname = "avoindata"
        elif "opendata" in hostname:
            hostname = "opendata"

        lang = helpers.lang() if helpers.lang() else "default"
        dict_key = hostname + "_" + lang

        logo = self.logos.get(dict_key, self.logos.get('default', None))

        if logo:
            return literal('<img src="%s" class="site-logo" />' % helpers.url_for_static("/images/logo/%s" % logo))
        else:
            return self._short_domain(hostname, default)

    def get_helpers(self):
        return {'short_domain': self._short_domain, 'get_menu_for_page': self._get_menu_for_page, 'site_logo': self._site_logo}
