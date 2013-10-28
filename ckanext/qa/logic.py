import logging

from ckan.plugins import PluginImplementations
from ckan.model import Package
from ckan.logic import NotFound, check_access, get_action
import ckan.new_authz
from ckan.lib.search import index_for

log = logging.getLogger(__name__)

def search_index_update(context, data_dict):
    model = context['model']
    session = context['session']
    user = context.get('user')

    if not ckan.new_authz.is_sysadmin(user):
        return {'success': False, 'msg': _('User %s not authorized to update harvest sources') % str(user)}
    #check_access('search_index_update', context, data_dict)

    pkg_dict = get_action('package_show')(
        {'model': model, 'ignore_auth': True, 'validate': False,
         'use_cache': False},
        data_dict)

    indexer = index_for('package')
    indexer.update_dict(pkg_dict)

    log.info('Search index updated for: %s', pkg_dict['name'])
