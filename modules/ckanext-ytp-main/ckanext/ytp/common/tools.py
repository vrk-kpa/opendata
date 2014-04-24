from ckan import model, plugins
import sys
import imp


def create_system_context():
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
    context['user'] = admin_user['name']
    return context


def get_original_method(module_name, method_name):
    """ Example get_original_method('ckan.logic.action.create', 'user_create') """
    __import__(module_name)
    imported_module = sys.modules[module_name]
    reimport_module = imp.load_compiled('%s.reimport' % module_name, imported_module.__file__)

    return getattr(reimport_module, method_name)
