from ckan import model
from ckan.common import request, c, response
from ckan.logic import get_action, NotFound
from ckan.lib import helpers
from ckan.controllers.package import PackageController
from ckan.lib.base import redirect


class YtpDatasetController(PackageController):
    def ytp_tag_autocomplete(self):
        """ CKAN autocomplete discards vocabulary_id from request.
            This is modification from tag_autocomplete function from CKAN.
            Takes vocabulary_id as parameter.
        """
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        vocabulary_id = request.params.get('vocabulary_id', None)
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session, 'user': c.user or c.author}
            data_dict = {'q': q, 'limit': limit}
            if vocabulary_id:
                data_dict['vocabulary_id'] = vocabulary_id
            try:
                tag_names = get_action('tag_autocomplete')(context, data_dict)
            except NotFound:
                pass  # return empty when vocabulary is not found
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names]
            }
        }

        status_int = 200
        response.status_int = status_int
        response.headers['Content-Type'] = 'application/json;charset=utf-8'
        return helpers.json.dumps(resultSet)

    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        """ Fake metadata creation. Change status to active and redirect to read. """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        data_dict = get_action('package_show')(context, {'id': id})
        data_dict['id'] = id
        data_dict['state'] = 'active'
        context['allow_state_change'] = True

        get_action('package_update')(context, data_dict)
        redirect(helpers.url_for(controller='package', action='read', id=id))
