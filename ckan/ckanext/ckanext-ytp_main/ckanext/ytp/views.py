from flask import Blueprint

import ckan.model as model
from ckan.common import config
from ckan.views.api import _finish_ok
from ckan.views.dataset import GroupView as CkanDatasetGroupView

from .model import MunicipalityBoundingBox
from ckan.plugins.toolkit import h, g, abort, request, get_action, NotAuthorized, ObjectNotFound, _
from ckan.views.feed import (_package_search, _parse_url_params, _navigation_urls, _feed_url, _alternate_url,
                            _create_atom_id, output_feed)


SITE_TITLE = config.get(u'ckan.site_title', u'CKAN')


def tag_autocomplete():
    """ CKAN autocomplete discards vocabulary_id from request.
        This is modification from tag_autocomplete function from CKAN.
        Takes vocabulary_id as parameter.
    """
    q = request.args.get('incomplete', '')
    limit = request.args.get('limit', 10)
    vocabulary_id = request.args.get('vocabulary_id', None)
    if vocabulary_id:
        from .plugin import create_vocabulary
        create_vocabulary(vocabulary_id)

    tag_names = []
    if q:
        context = {'model': model, 'session': model.Session, 'user': g.user or g.author}
        data_dict = {'q': q, 'limit': limit}
        if vocabulary_id:
            data_dict['vocabulary_id'] = vocabulary_id
        try:
            tag_names = get_action('tag_autocomplete')(context, data_dict)
        except ObjectNotFound:
            pass  # return empty when vocabulary is not found
    resultSet = {
        'ResultSet': {
            'Result': [{'Name': tag} for tag in tag_names]
        }
    }

    return _finish_ok(resultSet)


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


def get_all_locations():
    """Endpoint for getting all geocoded bounding boxes for Finnish municipalities"""
    all_bboxes = model.Session.query(MunicipalityBoundingBox).all()
    data = []
    for bbox in all_bboxes:
        data.append({'text': bbox.name, 'id': [bbox.lng_min, bbox.lat_min, bbox.lng_max, bbox.lat_max]})

    return _finish_ok({'results': data})


def recent_datasets_feed():
    data_dict, params = _parse_url_params()
    data_dict['q'] = u'*:*'
    data_dict['sort'] = 'metadata_created desc'

    item_count, results = _package_search(data_dict)

    navigation_urls = _navigation_urls(
        params,
        item_count=item_count,
        limit=data_dict['rows'],
        controller=u'ytp_main',
        action=u'recent_datasets_feed')

    feed_url = _feed_url(params, controller=u'ytp_main', action=u'recent_datasets_feed')

    alternate_url = _alternate_url(params)

    guid = _create_atom_id(u'/feeds/recent-datasets.atom')

    desc = u'Recently created datasets on %s' % SITE_TITLE

    return output_feed(
        results,
        feed_title=SITE_TITLE,
        feed_description=desc,
        feed_link=alternate_url,
        feed_guid=guid,
        feed_url=feed_url,
        navigation_urls=navigation_urls)


ytp_main = Blueprint('ytp_main', __name__)
ytp_main_dataset = Blueprint('ytp_main_dataset', __name__,
                             url_prefix='/dataset',
                             url_defaults={'package_type': 'dataset'})
ytp_main_dataset.add_url_rule(u'/groups/<id>', view_func=GroupView.as_view(str(u'groups')))
ytp_main.add_url_rule('/api/util/dataset/autocomplete', view_func=dataset_autocomplete)
ytp_main.add_url_rule('/api/2/util/dataset/autocomplete', view_func=dataset_autocomplete)
ytp_main.add_url_rule('/api/util/tag/autocomplete', view_func=tag_autocomplete)
ytp_main.add_url_rule('/api/2/util/tag/autocomplete', view_func=tag_autocomplete)
ytp_main.add_url_rule('/api/util/dataset/locations', view_func=get_all_locations)
ytp_main.add_url_rule('/feeds/recent-datasets.atom', methods=[u'GET'], view_func=recent_datasets_feed)


def get_blueprint():
    return [ytp_main, ytp_main_dataset]
