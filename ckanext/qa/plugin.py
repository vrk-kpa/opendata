import logging
import os

import ckan.model as model
import ckan.plugins as p
from ckan.lib.celery_app import celery
from ckan.model.types import make_uuid

from ckanext.archiver.interfaces import IPipe


log = logging.getLogger(__name__)


class QAPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(IPipe, inherit=True)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IReportCache)

    # IConfigurer

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        # Update config gets called before the IRoutes methods
        self.root_dir = config.get('ckanext.qa.url_root', '') # deprecated

    # IRoutes

    def before_map(self, map):
        # Redirect from some old URLs
        map.redirect('%s/qa' % self.root_dir,
                     '/data/report')
        map.redirect('%s/qa/dataset/{.*}' % self.root_dir,
                     '/data/report')
        map.redirect('%s/qa/organisation/{.*}' % self.root_dir,
                     '/data/report')
        map.redirect('/api/2/util/qa/{.*}' % self.root_dir,
                     '/data/report')
        map.redirect('%s/qa/organisation/broken_resource_links' % self.root_dir,
                     '/data/report/broken-links')
        map.redirect('%s/qa/organisation/broken_resource_links/:organization' % self.root_dir,
                     '/data/report/broken-links/:organizations')
        map.redirect('%s/qa/organisation/scores' % self.root_dir,
                     '/data/report/openness')
        map.redirect('%s/qa/organisation/scores/:organization' % self.root_dir,
                     '/data/report/openness/:organizations')

        # Link checker
        res = 'ckanext.qa.controllers.qa_resource:QAResourceController'
        map.connect('qa_resource_checklink', '/qa/link_checker',
                    conditions=dict(method=['GET']),
                    controller=res,
                    action='check_link')

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
        return find_logic_functions('ckanext.qa.logic_action')

    # IAuthFunctions

    def get_auth_functions(self):
        return find_logic_functions('ckanext.qa.logic_auth')

    # IReportCache

    def register_reports(self):
        """Register details of an extension's reports"""
        from ckanext.qa import reports
        return [reports.openness_report_info]


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


def find_logic_functions(module_path):
    '''Given a python module containing logic functions, it returns a dict of
    them by their name.
    This is based on _get_logic_functions in ckanext-harvest
    '''
    logic_functions = {}
    module = __import__(module_path)
    for part in module_path.split('.')[1:]:
        module = getattr(module, part)
    for key, value in module.__dict__.items():
        if not key.startswith('_') and (hasattr(value, '__call__')
                and (value.__module__ == module_path)):
            logic_functions[key] = value
    return logic_functions
