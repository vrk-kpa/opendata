# -*- coding: utf-8 -*-

from flask import Blueprint
from ckanext.showcase import views, utils as showcase_utils

import utils as utils

def read(id):
    return utils.read_view(id)

def index():
    return utils.index(showcase_utils.DATASET_TYPE_NAME)

showcase = Blueprint(u'sixodp_showcase', __name__)

showcase.add_url_rule('/showcase', view_func=index)
# showcase.add_url_rule('/showcase/new', view_func=CreateView.as_view('new'))
# showcase.add_url_rule('/showcase/delete/<id>',
#                       view_func=delete,
#                       methods=[u'GET', u'POST'])
showcase.add_url_rule('/showcase/<id>', view_func=read)
# showcase.add_url_rule('/showcase/edit/<id>',
#                       view_func=EditView.as_view('edit'),
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/showcase/manage_datasets/<id>',
#                       view_func=manage_datasets,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/dataset/showcases/<id>',
#                       view_func=dataset_showcase_list,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/ckan-admin/showcase_admins',
#                       view_func=admins,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/ckan-admin/showcase_admin_remove',
#                       view_func=admin_remove,
#                       methods=[u'GET', u'POST'])
# showcase.add_url_rule('/showcase_upload',
#                       view_func=upload,
#                       methods=[u'POST'])


def get_blueprints():
    return [showcase] + views.get_blueprints()