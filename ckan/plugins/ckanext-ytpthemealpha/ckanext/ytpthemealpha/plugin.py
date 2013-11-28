from ckan import plugins as p
from ckan.plugins import implements
from ckan.plugins.interfaces import IConfigurer
from ckan.plugins import toolkit as tk


class YTPThemeAlphaPlugin(p.SingletonPlugin):
  
    implements(IConfigurer)

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public/css/', 'ytp_css')
        tk.add_resource('public/js/', 'ytp_js')