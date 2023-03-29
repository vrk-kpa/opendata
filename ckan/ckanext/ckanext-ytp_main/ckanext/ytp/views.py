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
    dataset_limit = int(config.get(u'ckan.datasets_per_page', 20))
    organization_limit = int(config.get(u'ckan.organizations_per_page', 5))
    sort_by = request.args.get(u'sort', "score desc, metadata_created desc")

    chosen_filter = "all"
    # Usually not passed in this way, instead submitted in the form 
    # (we also treat organizations as a dataset type in this scenario)
    dataset_type = request.args.get(u'dataset_type', 'all')

    # Post request contains filters and page numbers that the user has selected
    if request.method == 'POST':
        # Get the page number from the request
        page = int(request.form.get('page', 1))
        sort_by = request.form.get('sort', "score desc, metadata_created desc")
        chosen_filter = request.form.get('filter', 'all')
        dataset_type = request.form.get('filter', 'all')

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

    # Organizations require a bit different search term and treatment if they are the only thing searched
    if dataset_type == 'organization':
        # if user is searching only for organizations, we want to display more organizations than 5
        organization_limit = 20
        fq = 'entity_type:organization'
    else:
        all_types = 'dataset_type:dataset OR dataset_type:apiset OR dataset_type:showcase OR entity_type:organization'
        allowed_types = ['dataset', 'apiset', 'showcase']
        fq = f'dataset_type:{dataset_type}' if dataset_type in allowed_types else all_types

    data_dict = {
        'q': q,
        'datasets.rows': dataset_limit,
        'organizations.rows': organization_limit,
        'datasets.start': (page - 1) * dataset_limit,
        'organizations.start': (page - 1) * organization_limit,
        'extras': {},
        'sort': sort_string,
        'defType': 'edismax',
        'mm': 0,
        'fq': fq
    }

    # Get the results that will be passed to the template
    total_results = get_action('site_search')(context, data_dict)

    # Get the specific amount of datasets, apisets and showcases + organizations 
    result_count = {
        'dataset': 0,
        'apiset': 0,
        'showcase': 0,
        'organization': 0,
        'all': 0
    }

    # Organizations and datasets (datasets, apis, showcases) are packaged separately in the results
    datasets = total_results.get('datasets', {})
    organizations = total_results.get('organizations', {})
    item_count = datasets.get('count', 0) + organizations.get('count', 0)

    # get the amount of results for each type of resource and resources in separate queries
    only_datasets = get_action('package_search')(context, {'q': q, 'fq': 'dataset_type:dataset'})
    dataset_count = only_datasets.get('count', 0)
    only_apisets = get_action('package_search')(context, {'q': q, 'fq': 'dataset_type:apiset'})
    apiset_count = only_apisets.get('count', 0)
    only_showcases = get_action('package_search')(context, {'q': q, 'fq': 'dataset_type:showcase'})
    showcase_count = only_showcases.get('count', 0)
    only_organizations = get_action('organization_search')(context, {'q': q})
    organization_count = only_organizations.get('count', 0)

    # combine the results
    result_count['dataset'] = dataset_count
    result_count['apiset'] = apiset_count
    result_count['showcase'] = showcase_count
    result_count['organization'] = organization_count
    result_count['all'] = dataset_count + apiset_count + showcase_count + organization_count

    dataset_sets = datasets.get('results', [])
    organization_sets = organizations.get('results', [])

    # get additional info for the organizations
    for organization in organization_sets:
        # Parse the organization description from the extras 
        org_extras = organization.get('extras', [])
        t = next(filter(lambda t: t.get('key') == 'description_translated', org_extras), None)
        if t:
            translations = t.get('value')
            new_description_translated = json.loads(translations)
            # add the translated description field
            organization['description_translated'] = new_description_translated

    # combine organizations and other resources
    combined_results = organization_sets + dataset_sets

    # determine the page amount
    if dataset_type == 'all':
        # count all but organizations
        datasets = int(result_count.get('all', 0)) - int(result_count.get('organization', 0))
    else:
        datasets = int(result_count.get(dataset_type, 0))

    # Use the higher count for the number of total pages
    dataset_pages = int(math.ceil(datasets / dataset_limit))
    organization_pages = int(math.ceil(float(result_count.get('organization', 0)) / organization_limit))
    total_pages = dataset_pages if dataset_pages > organization_pages else organization_pages

    g.general_search = {
            u'q': q,
            u'total_results': combined_results,
            u'result_count': result_count,
            u'item_count': item_count,
            u"last_query": params_to_dict(request.form),
            u'filter': chosen_filter,
            u'page': page,
            u'sort_string': sort_string,
            u'total_pages': total_pages,
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
