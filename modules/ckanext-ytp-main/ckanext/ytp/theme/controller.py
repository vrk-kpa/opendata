import ckan.lib.base as base
from pylons import config
from paste.deploy.converters import asbool

render = base.render
abort = base.abort


class YtpThemeController(base.BaseController):
    def new_template(self):
        if asbool(config.get('ckanext.ytp.theme.show_postit_demo', True)):
            return render('postit_templates/new.html')
        else:
            return abort(404)

    def return_template(self):
        if asbool(config.get('ckanext.ytp.theme.show_postit_demo', True)):
            return render('postit_templates/return.html')
        else:
            return abort(404)
