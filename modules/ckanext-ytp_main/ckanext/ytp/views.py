import ckan.model as model
from ckan.common import g, request
from ckan.logic import get_action
from ckan.views.api import _finish_ok


def dataset_autocomplete():
    q = request.args.get(u'incomplete', u'')
    limit = request.args.get(u'limit', 10)
    package_type = request.args.get(u'package_type', '')
    package_dicts = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

        data_dict = {u'q': q, u'limit': limit, u'package_type': package_type}

        package_dicts = get_action(
            u'package_autocomplete')(context, data_dict)

    resultSet = {u'ResultSet': {u'Result': package_dicts}}
    return _finish_ok(resultSet)
