import os
from logging import getLogger

from genshi.input import HTML
from genshi.filters import Transformer

import ckan.lib.helpers as h

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes, IConfigurer
from ckan.plugins import IConfigurable, IGenshiStreamFilter

import html

log = getLogger(__name__)

class QA(SingletonPlugin):
    
    implements(IConfigurable)
    implements(IGenshiStreamFilter)
    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)
    
    def configure(self, config):
        self.enable_organisations = config.get('qa.organisations', True)

    def filter(self, stream):
        if self.enable_organisations:
            from pylons import request, tmpl_context as c
            routes = request.environ.get('pylons.routes_dict')
        
            data = dict(link = h.link_to("Organizations who have published packages with broken resource links.",\
                h.url_for(controller='qa',\
                action='organisations_with_broken_resource_links')
            ))

            if routes.get('controller') == 'ckanext.qa.controllers.view:ViewController'\
               and routes.get('action') == 'index':
                stream = stream | Transformer('body//div[@class="qa-content"]')\
                    .append(HTML(html.ORGANIZATION_LINK % data))
                        
        return stream
        
    def before_map(self, map):
        map.connect('qa', '/qa',
            controller='ckanext.qa.controllers.qa_home:QAHomeController',
            action='index')
            
        map.connect('qa_package', '/qa/package/',
            controller='ckanext.qa.controllers.qa_package:QAPackageController')

        map.connect('qa_package_action', '/qa/package/{action}',
            controller='ckanext.qa.controllers.qa_package:QAPackageController')

        map.connect('qa_organisation', '/qa/organisation/',
            controller='ckanext.qa.controllers.qa_organisation:QAOrganisationController')

        map.connect('qa_organisation_action', '/qa/organisation/{action}',
            controller='ckanext.qa.controllers.qa_organisation:QAOrganisationController')
                
        map.connect('qa_organisation_action_id', '/qa/organisation/{action}/:id',
            controller='ckanext.qa.controllers.qa_organisation:QAOrganisationController')

        map.connect('qa_api', '/api/2/util/qa/{action}',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController')
                
        map.connect('qa_api_resource_formatted',
                    '/api/2/util/qa/{action}/:(id).:(format)',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController')
                
        map.connect('qa_api_resource', '/api/2/util/qa/{action}/:id',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController')
                
        return map

    def update_config(self, config):
        here = os.path.dirname(__file__)

        template_dir = os.path.join(here, 'templates')
        public_dir = os.path.join(here, 'public')
        
        if config.get('extra_template_paths'):
            config['extra_template_paths'] += ','+template_dir
        else:
            config['extra_template_paths'] = template_dir
        if config.get('extra_public_paths'):
            config['extra_public_paths'] += ','+public_dir
        else:
            config['extra_public_paths'] = public_dir

