import logging
import types

import ckan.model as model
import ckan.plugins as p

from ckanext.archiver.interfaces import IPipe
from ckanext.qa.logic import action, auth
from ckanext.qa.model import QA, aggregate_qa_for_a_dataset
from ckanext.qa import helpers
from ckanext.qa import lib
from ckanext.report.interfaces import IReport


log = logging.getLogger(__name__)


class QAPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(IPipe, inherit=True)
    p.implements(IReport)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')

    # IRoutes

    def before_map(self, map):
        # Link checker - deprecated
        res = 'ckanext.qa.controllers:LinkCheckerController'
        map.connect('qa_resource_checklink', '/qa/link_checker',
                    conditions=dict(method=['GET']),
                    controller=res,
                    action='check_link')
        return map

    # IPipe

    def receive_data(self, operation, queue, **params):
        '''Receive notification from ckan-archiver that a resource has been
        archived.
        '''
        if not operation == 'archived':
            return
        resource_id = params['resource_id']

        resource = model.Resource.get(resource_id)
        assert resource

        lib.create_qa_update_task(resource, queue=queue)

    # IReport

    def register_reports(self):
        """Register details of an extension's reports"""
        from ckanext.qa import reports
        return [reports.openness_report_info]

    # IActions

    def get_actions(self):
        return get_functions(action)

    # IAuthFunctions

    def get_auth_functions(self):
        return get_functions(auth)

    # ITemplateHelpers

    def get_helpers(self):
        return get_functions(helpers)

    # IPackageController

    def after_show(self, context, pkg_dict):
        # Insert the qa info into the package_dict so that it is
        # available on the API.
        # When you edit the dataset, these values will not show in the form,
        # it they will be saved in the resources (not the dataset). I can't see
        # and easy way to stop this, but I think it is harmless. It will get
        # overwritten here when output again.
        qa_objs = QA.get_for_package(pkg_dict['id'])
        if not qa_objs:
            return
        # dataset
        dataset_qa = aggregate_qa_for_a_dataset(qa_objs)
        pkg_dict['qa'] = dataset_qa
        # resources
        qa_by_res_id = dict((a.resource_id, a) for a in qa_objs)
        if pkg_dict.get('resources', None):
            for res in pkg_dict['resources']:
                qa = qa_by_res_id.get(res['id'])
                if qa:
                    qa_dict = qa.as_dict()
                    del qa_dict['id']
                    del qa_dict['package_id']
                    del qa_dict['resource_id']
                    res['qa'] = qa_dict


def get_functions(module):
    return dict((name, function) for name, function
                in module.__dict__.items()
                if isinstance(function, types.FunctionType)
                and name[0] != '_')
