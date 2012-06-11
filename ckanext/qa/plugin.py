import json
import datetime
from genshi.input import HTML
from genshi.filters import Transformer
from pylons import request, tmpl_context as c
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model
import ckan.plugins as p
import ckan.lib.celery_app as celery_app
from ckan.model.types import make_uuid
import html
import reports

resource_dictize = model_dictize.resource_dictize
send_task = celery_app.celery.send_task


class QAPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable)
    p.implements(p.IGenshiStreamFilter)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(p.IResourceUrlChange)

    def configure(self, config):
        self.site_url = config.get('ckan.site_url')

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
        home = 'ckanext.qa.controllers.qa_home:QAHomeController'
        pkg = 'ckanext.qa.controllers.qa_package:QAPackageController'
        org = 'ckanext.qa.controllers.qa_organisation:QAOrganisationController'
        res = 'ckanext.qa.controllers.qa_resource:QAResourceController'
        api = 'ckanext.qa.controllers.qa_api:ApiController'

        map.connect('qa', '/qa', controller=home, action='index')

        map.connect('qa_dataset', '/qa/dataset/',
                    controller=pkg, action='index')
        map.connect('qa_dataset_action', '/qa/dataset/{action}',
                    controller=pkg)

        map.connect('qa_organisation', '/qa/organisation/',
                    controller=org)
        map.connect('qa_organisation_action', '/qa/organisation/{action}',
                    controller=org)
        map.connect('qa_organisation_action_id',
                    '/qa/organisation/{action}/:id',
                    controller=org)

        map.connect('qa_resource_checklink', '/qa/link_checker',
                    conditions=dict(method=['GET']),
                    controller=res,
                    action='check_link')

        map.connect('qa_api', '/api/2/util/qa/{action}',
                    conditions=dict(method=['GET']),
                    controller=api)
        map.connect('qa_api_resource_formatted',
                    '/api/2/util/qa/{action}/:(id).:(format)',
                    conditions=dict(method=['GET']),
                    controller=api)
        map.connect('qa_api_resources_formatted',
                    '/api/2/util/qa/{action}/all.:(format)',
                    conditions=dict(method=['GET']),
                    controller=api)
        map.connect('qa_api_resource', '/api/2/util/qa/{action}/:id',
                    conditions=dict(method=['GET']),
                    controller=api)
        map.connect('qa_api_resources_available',
                    '/api/2/util/qa/resources_available/{id}',
                    conditions=dict(method=['GET']),
                    controller=api,
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
        user = p.toolkit.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )
        context = json.dumps({
            'site_url': self.site_url,
            'apikey': user.get('apikey')
        })

        resource_dict = resource_dictize(resource, {'model': model})
        package = resource.related_packages()[0]
        resource_dict['is_open'] = package.isopen()

        data = json.dumps(resource_dict)

        task_id = make_uuid()
        task_status = {
            'entity_id': resource.id,
            'entity_type': u'resource',
            'task_type': u'qa',
            'key': u'celery_task_id',
            'value': task_id,
            'error': u'',
            'last_updated': datetime.datetime.now().isoformat()
        }
        task_context = {
            'model': model,
            'user': user.get('name'),
        }

        p.toolkit.get_action('task_status_update')(task_context, task_status)
        send_task('qa.update', args=[context, data], task_id=task_id)

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')
        stream = stream | Transformer('head').append(HTML(html.HEAD_CODE))

        if (routes.get('controller') == 'package' and
            routes.get('action') == 'resource_read'):

            star_html = self.get_star_html(c.resource.get('id'))
            if star_html:
                stream = stream | Transformer('body//div[@class="quick-info"]//dl')\
                    .append(HTML(html.DL_HTML % star_html))

        if (routes.get('controller') == 'package' and
            routes.get('action') == 'read' and
            c.pkg.id):

            for resource in c.pkg_dict.get('resources', []):
                resource_id = resource.get('id')
                star_html = self.get_star_html(resource_id)
                if star_html:
                    stream = stream | Transformer('body//div[@id="%s"]//p[@class="extra-links"]' % resource_id)\
                        .append(HTML(star_html))

        return stream

    def get_star_html(self, resource_id):
        report = reports.resource_five_stars(resource_id)
        stars = report.get('openness_score', -1)
        if stars >= 0:
            reason = report.get('openness_score_reason')
            return html.get_star_html(stars, reason)
        return None
