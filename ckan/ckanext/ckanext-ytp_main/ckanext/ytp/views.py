from flask import Blueprint

import ckan.model as model
from ckan.common import config
from ckan.views.api import _finish_ok
from ckan.views.dataset import GroupView as CkanDatasetGroupView
import ckan.lib.base as base

from .model import MunicipalityBoundingBox
from ckan.plugins.toolkit import h, g, abort, request, get_action, NotAuthorized, ObjectNotFound, _
from ckan.views.feed import (_package_search, _parse_url_params, _navigation_urls, _feed_url, _alternate_url,
                            _create_atom_id, output_feed)


import math
import logging
import json


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






def _tag_string_to_list(tag_string):
    """This is used to change tags from a sting to a list of dicts.
    """
    out = []
    for tag in tag_string.split(u','):
        tag = tag.strip()
        if tag:
            out.append({u'name': tag, u'state': u'active'})
    return out




# Based on search() from ckan 2.9
def general_search():

    extra_vars = {}

    context = {
        u'model': model,
        u'user': g.user,
        u'auth_user_obj': g.userobj
    }


    # unicode format (decoded from utf8)
    extra_vars[u'q'] = q = request.args.get(u'q', u'')
    extra_vars['query_error'] = False

    # Get the page number from parameters if it's provided (maybe this can be removed?)
    page = int(request.params.get('page', 1))
    logging.warning(f"Page: {page}")

    limit = int(config.get(u'ckan.datasets_per_page', 10))
    sort_by = request.args.get(u'sort', None)

    chosen_filter = "all"
    # Usually not passed in this way, instead submitted in the form
    dataset_type = request.args.get(u'dataset_type', None)


    # Post request contains filters and page numbers that the user has selected
    if request.method == 'POST':
        # Get the page number from the request
        page = int(request.form.get('page', 1))
        sort_by = request.form.get('sort', "score desc, metadata_created desc")
        chosen_filter = request.form.get('filter', 'all')
        dataset_type = request.form.get('filter', 'all')
        # logging.warning(sort_by)
        # logging.warning(chosen_filter)
        

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in request.args.items(multi=True)
                     if k != u'page']

    params_nosort = [(k, v) for k, v in params_nopage if k != u'sort']

    allowed_sorting = [
        'score desc, metadata_created desc',
        'title_string asc',
        'title_string desc',
        'metadata_modified desc',
        'metadata_created asc',
        'metadata_created desc',
        'views_recent desc'
    ]


    sort_string = sort_by if sort_by in allowed_sorting else "score desc, metadata_created desc"

    # http://localhost/data/fi/search?sort=title_string
    logging.warning(f"Given sorting: {sort_by}")
    logging.warning(f"used sorting: {sort_string}")

    # Add organizations here when they are implemented
    all_types = 'dataset_type:dataset OR dataset_type:apiset OR dataset_type:showcase'
    allowed_types = ['dataset', 'apiset', 'showcase']
    fq = f'dataset_type:{dataset_type}' if dataset_type in allowed_types else all_types

    data_dict = {
        'q': q,
        'rows': limit,
        'start': (page - 1) * limit,
        'extras': {},
        'sort': sort_string,
        'defType': 'edismax',
        'mm': 0,
        'fq': fq
    }

    # Get the results that will be passed to the template
    total_results = get_action('package_search')(context, data_dict)
    logging.warning(json.dumps(total_results))


    # Get the specific amount of datasets, apisets and showcases (+ organizations when implemented)
    result_count = {
        'dataset': 0,
        'apiset': 0,
        'showcase': 0,
        'all': 0
    }

    # get the amount of results for each type
    for key, value in result_count.items():
        simple_dict = {
        'q': q,
        'fq': ""
        }
        if key != 'all':
            simple_dict['fq'] = f"dataset_type:{key}"
            sets = get_action('package_search')(context, simple_dict)
            count = sets.get('count', 0)
            result_count[key] = count
            result_count['all'] += count
    

    g.general_search = {
            u'q': q,
            u'total_results': total_results,
            u'result_count': result_count,
            u'item_count': total_results.get('count', 0),
            u"last_query": params_to_dict(request.form),
            u'filter': chosen_filter,
            u'page': page,
            u'sort_string': sort_string,
            u'total_pages': int(math.ceil(float(result_count.get(dataset_type, 0)) / float(limit))),
    }
    g.general_search['last_query']['page'] = page

    return base.render(
        u'general_search/index.html')


def params_to_dict(params):
    new_dict = {}
    for i in params:
        key = i
        if not hasattr(new_dict, key):
            value = params.getlist(i)
            new_dict.setdefault(key, value)
    return new_dict


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
ytp_main.add_url_rule('/search',  methods=[u'GET', 'POST'], view_func=general_search)


def get_blueprint():
    return [ytp_main, ytp_main_dataset]
