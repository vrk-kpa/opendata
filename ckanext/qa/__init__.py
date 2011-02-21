# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

import os
from logging import getLogger
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes, IConfigurer

log = getLogger(__name__)

class QA(SingletonPlugin):
    
    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)
    
    def before_map(self, map):
        map.connect('qa', '/qa',
            controller='ckanext.qa.controllers.view:ViewController',
            action='index')
            
        map.connect('qa_action', '/qa/{action}',
            controller='ckanext.qa.controllers.view:ViewController')
            
        map.connect('qa_api', '/api/2/util/qa/{action}',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.api:ApiController')
                
        map.connect('qa_api_resource', '/api/2/util/qa/{action}/:id',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.api:ApiController')

        return map

    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))

        template_dir = os.path.join(rootdir, 'templates')
        public_dir = os.path.join(rootdir, 'public')
        
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])
        config['extra_public_paths'] = ','.join([public_dir,
                config.get('extra_public_paths', '')])

