from flask import Blueprint

import ckan.model as model
from ckan.views.api import _finish_ok
from ckan.views.dataset import GroupView as CkanDatasetGroupView

from ckan.plugins.toolkit import h, g, abort, request, get_action, NotAuthorized, ObjectNotFound, _


def dataset_autocomplete():
    q = request.args.get('incomplete', '')
    limit = request.args.get('limit', 10)
    package_type = request.args.get('package_type', '')
    package_dicts = []
    if q:
        context = {'model': model, 'session': model.Session,
                   'user': g.user, 'auth_user_obj': g.userobj}

        data_dict = {'q': q, 'limit': limit, 'package_type': package_type}

        package_dicts = get_action(
            'package_autocomplete')(context, data_dict)

    resultSet = {'ResultSet': {'Result': package_dicts}}
    return _finish_ok(resultSet)


class GroupView(CkanDatasetGroupView):
    def post(self, package_type, id):
        context, pkg_dict = self._prepare(id)

        category_list = request.form.getlist('categories')
        group_list = [{'name': c} for c in category_list]
        try:
            get_action('package_patch')(context, {"id": id, "groups": group_list, "categories": category_list})
            return h.redirect_to('dataset_groups', id=id)
        except (ObjectNotFound, NotAuthorized):
            return abort(404, _('Dataset not found'))


ytp_main = Blueprint('ytp_main', __name__)
ytp_main_dataset = Blueprint('ytp_main_dataset', __name__,
                             url_prefix='/dataset',
                             url_defaults={'package_type': 'dataset'})
ytp_main_dataset.add_url_rule(u'/groups/<id>', view_func=GroupView.as_view(str(u'groups')))
ytp_main.add_url_rule('/api/util/dataset/autocomplete', view_func=dataset_autocomplete)


def get_blueprint():
    return [ytp_main, ytp_main_dataset]
