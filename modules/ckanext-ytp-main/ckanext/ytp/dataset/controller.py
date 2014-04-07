from ckan.lib import base
from ckan import model
from ckan.common import request, c, response
from ckan.logic import get_action, NotFound
from ckan.lib import helpers


class YtpDatasetController(base.BaseController):
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
