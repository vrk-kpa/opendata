import ckan.model as model
from ckan.common import g, request
from ckan.logic import get_action
from ckan.views.api import _finish_ok


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
