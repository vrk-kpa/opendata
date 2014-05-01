import json
import datetime
import logging
import os

from genshi.input import HTML
from genshi.filters import Transformer
from pylons import request, tmpl_context as c

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model
import ckan.plugins as p
import ckan.lib.helpers as h
import ckan.lib.celery_app as celery_app
from ckan.lib.celery_app import celery
import ckan.plugins.toolkit as t
from ckan.model.types import make_uuid

import html
import reports
import logic

from ckanext.archiver.interfaces import IPipe

resource_dictize = model_dictize.resource_dictize
send_task = celery_app.celery.send_task

log = logging.getLogger(__name__)


class QAPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(IPipe, inherit=True)
    #p.implements(p.IDomainObjectModification, inherit=True)
    #p.implements(p.IResourceUrlChange)
    p.implements(p.IActions)
    p.implements(p.IReportCache)

    # IConfigurer

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
        # Update config gets called before the IRoutes methods
        self.root_dir = config.get('ckanext.qa.url_root', '')

    # IRoutes

    def before_map(self, map):
        home = 'ckanext.qa.controllers.qa_home:QAHomeController'
        pkg = 'ckanext.qa.controllers.qa_package:QAPackageController'
        org = 'ckanext.qa.controllers.qa_organisation:QAOrganisationController'
        res = 'ckanext.qa.controllers.qa_resource:QAResourceController'
        api = 'ckanext.qa.controllers.qa_api:ApiController'

        map.connect('qa', '%s/qa' % self.root_dir, controller=home, action='index')

        map.connect('qa_dataset', '%s/qa/dataset/' % self.root_dir,
                    controller=pkg, action='index')
        map.connect('qa_dataset_action', '%s/qa/dataset/{action}'  % self.root_dir,
                    controller=pkg)

        map.connect('qa_organisation', '%s/qa/organisation/'  % self.root_dir,
                    controller=org, action='index')
        map.connect('qa_organisation_action', '%s/qa/organisation/{action}'  % self.root_dir,
                    controller=org)
        map.connect('qa_organisation_action_id',
                    '%s/qa/organisation/{action}/:id'  % self.root_dir,
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

    # IPipe

    def receive_data(self, operation, **params):
        '''Receive notification from ckan-archiver that a resource has been archived.'''
        if not operation == 'archived':
            return
        resource_id = params['resource_id']
        #cache_filepath = params['cached_filepath']

        resource = model.Resource.get(resource_id)
        assert resource

        create_qa_update_task(resource, queue='priority')

    # IActions

    def get_actions(self):
        return {
            'search_index_update': logic.search_index_update,
            'qa_resource_show': logic.qa_resource_show,
            'qa_package_show': logic.qa_package_show,
            }

    # IReportCache

    def register_reports(self):
        from ckanext.qa import reports
        return [] # HACKfor now
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


def create_qa_update_package_task(package, queue):
    from pylons import config
    task_id = '%s-%s' % (package.name, make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config.__file__)
    celery.send_task('qa.update_package', args=[ckan_ini_filepath, package.id],
                     task_id=task_id, queue=queue)
    log.debug('QA of package put into celery queue %s: %s', queue, package.name)

def create_qa_update_task(resource, queue):
    from pylons import config
    package = resource.resource_group.package
    task_id = '%s/%s/%s' % (package.name, resource.id[:4], make_uuid()[:4])
    ckan_ini_filepath = os.path.abspath(config.__file__)
    celery.send_task('qa.update', args=[ckan_ini_filepath, resource.id],
                     task_id=task_id, queue=queue)
    log.debug('QA of resource put into celery queue %s: %s/%s url=%r', queue, package.name, resource.id, resource.url)

