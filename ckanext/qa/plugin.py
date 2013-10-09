import json
import datetime
import logging

from genshi.input import HTML
from genshi.filters import Transformer
from pylons import request, tmpl_context as c

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model
import ckan.plugins as p
import ckan.lib.helpers as h
import ckan.lib.celery_app as celery_app
import ckan.plugins.toolkit as t
from ckan.model.types import make_uuid
from ckanext.qa.lib import get_site_url, get_user_and_context

import html
import reports
import logic

resource_dictize = model_dictize.resource_dictize
send_task = celery_app.celery.send_task

log = logging.getLogger(__name__)

class QAPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(p.IResourceUrlChange)
    p.implements(p.IActions)
    p.implements(p.ICachedReport)

    def configure(self, config):
        self.site_url = get_site_url(config)

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
                    controller=org, action='index')
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
                # Resource created
                self._create_task(entity)
        else:
            # Resource URL has changed.
            # If operation is None, resource URL has been changed because the
            # notify function in IResourceUrlChange only takes 1 parameter
            self._create_task(entity)

    def _create_task(self, resource):
        user, context = get_user_and_context(self.site_url)

        resource_dict = resource_dictize(resource, {'model': model})
        pkg_id = resource.resource_group.package.id if resource.resource_group else None
        resource_dict['package'] = pkg_id

        related_packages = resource.related_packages()
        if related_packages:
            resource_dict['is_open'] = related_packages[0].isopen()

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

        queue = 'priority'
        p.toolkit.get_action('task_status_update')(task_context, task_status)
        send_task('qa.update', args=[context, data], task_id=task_id, queue=queue)

        log.debug('QA check for resource put into celery queue %s: %s url=%r',
                  queue, resource.id, resource_dict.get('url'))

    def get_star_html(self, resource_id):
        report = reports.resource_five_stars(resource_id)
        stars = report.get('openness_score', -1)
        if stars >= 0:
            reason = report.get('openness_score_reason')
            return html.get_star_html(stars, reason)
        return None

    def get_actions(self):
        return {
            'search_index_update': logic.search_index_update,
            }

    def register_reports(self):
        """
        This method will be called so that the plugin can register the
        reports it wants run.  The reports will then be executed on a
        24 hour schedule and the appropriate tasks called.

        This call should return a dictionary, where the key is a description
        and the value should be the function to run. This function should
        take no parameters and return nothing.
        """
        from ckanext.qa.reports import cached_reports
        return { 'Cached QA Reports': cached_reports }

    def list_report_keys(self):
        """
        Returns a list of the reports that the plugin can generate by
        returning each key name as an item in a list.
        """
        return ['broken-link-report', 'broken-link-report-withsub',
                'openness-report', 'openness-report-withsub',
                'organisation_score_summaries',
                'organisations_with_broken_resource_links']
