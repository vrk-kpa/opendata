import os
import json
from datetime import datetime
from genshi.input import HTML
from genshi.filters import Transformer
from pylons import request, tmpl_context as c
from ckan import model
from ckan.model.types import make_uuid
import ckan.lib.helpers as h
from ckan.lib.dictization.model_dictize import resource_dictize
from ckan.plugins import implements, SingletonPlugin, IRoutes, IConfigurer, \
    IConfigurable, IGenshiStreamFilter, IResourceUrlChange, IDomainObjectModification
from ckan.logic import get_action
from ckan.lib.celery_app import celery

import html

class QAPlugin(SingletonPlugin):
    implements(IConfigurable)
    implements(IGenshiStreamFilter)
    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IDomainObjectModification, inherit=True)
    implements(IResourceUrlChange)
    
    def configure(self, config):
        self.enable_organisations = config.get('qa.organisations', True)
        self.site_url = config.get('ckan.site_url')

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
        
    def before_map(self, map):
        map.connect('qa', '/qa',
            controller='ckanext.qa.controllers.qa_home:QAHomeController',
            action='index')
            
        map.connect('qa_dataset', '/qa/dataset/',
            controller='ckanext.qa.controllers.qa_package:QAPackageController')

        map.connect('qa_dataset_action', '/qa/dataset/{action}',
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
                
        map.connect('qa_api_resources_formatted',
                    '/api/2/util/qa/{action}/all.:(format)',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController')

        map.connect('qa_api_resource', '/api/2/util/qa/{action}/:id',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController')

        map.connect('qa_api_resources_available', '/api/2/util/qa/resources_available/{id}',
            conditions=dict(method=['GET']),
            controller='ckanext.qa.controllers.qa_api:ApiController',
            action='resources_available')
                
        return map

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Resource):
            return
        
        if operation:
            if operation == model.DomainObjectOperation.new:
                self._create_task(entity)
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            self._create_task(entity)

    def _create_task(self, resource):
        user = get_action('get_site_user')({'model': model,
                                            'ignore_auth': True,
                                            'defer_commit': True}, {})
        context = json.dumps({
            'site_url': self.site_url,
            'apikey': user.get('apikey')
        })
        data = json.dumps(resource_dictize(resource, {'model': model}))

        task_id = make_uuid()
        task_status = {
            'entity_id': resource.id,
            'entity_type': u'resource',
            'task_type': u'qa',
            'key': u'celery_task_id',
            'value': task_id,
            'error': u'',
            'last_updated': datetime.now().isoformat()
        }
        task_context = {
            'model': model, 
            'user': user.get('name'),
        }
        
        get_action('task_status_update')(task_context, task_status)
        celery.send_task("qa.update", args=[context, data], task_id=task_id)

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')

        stream = stream | Transformer('head').append(HTML(html.HEAD_CODE))
        
        if routes.get('controller') == 'package' \
            and routes.get('action') == 'resource_read':

            star_html = self.get_star_html(c.resource.get('id'))
            if star_html:
                stream = stream | Transformer('body//div[@class="quick-info"]//dl')\
                    .append(HTML(html.DL_HTML % star_html))

        if routes.get('controller') == 'package' \
            and routes.get('action') == 'read' \
            and c.pkg.id:

            for resource in c.pkg_dict.get('resources',[]):
                resource_id = resource.get('id')
                star_html = self.get_star_html(resource_id)
                if star_html:
                    stream = stream | Transformer('body//div[@id="%s"]//p[@class="extra-links"]' % resource_id)\
                        .append(HTML(star_html))

        # show organization info
        if self.enable_organisations:
            if(routes.get('controller') == 'ckanext.qa.controllers.view:ViewController'
               and routes.get('action') == 'index'):

                link_text = "Organizations who have published datasets with broken resource links."
                data = dict(link = h.link_to(link_text,
                    h.url_for(controller='ckanext.qa.controllers.qa_organisation:QAOrganisationController',
                        action='broken_resource_links')
                ))

                stream = stream | Transformer('body//div[@class="qa-content"]')\
                    .append(HTML(html.ORGANIZATION_LINK % data))

        return stream

    def get_star_html(self, resource_id):
        from ckanext.qa import reports

        report = reports.resource_five_stars(resource_id)

        stars = report.get('openness_score', -1)
        if stars >= 0:
            reason = report.get('openness_score_reason')
            return html.get_star_html(stars, reason)
        return None

