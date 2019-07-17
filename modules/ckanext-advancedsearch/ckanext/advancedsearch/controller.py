import ckan.lib.base as base
from ckan.common import c
from ckan.lib import helpers as h
from ckan.lib.base import render
from ckan.logic import get_action


class YtpAdvancedSearchController(base.BaseController):
    def search(self):
        from ckan import model

        context = {
            'model': model,
            'session': model.Session,
            'user': c.user
        }

        # TODO: get the page from the url
        page = 1
        limit = 2

        data_dict = {
            'q': '*:*',
            'rows': limit,
            'start': (page - 1) * limit,
            'extras': {}
        }

        query = get_action('package_search')(context, data_dict)

        def make_pager_url(q=None, page=None):
            ctrlr = 'ckanext.advancedsearch.controller:YtpAdvancedSearchController'
            url = h.url_for(controller=ctrlr, action='search')
            return url + u'?page=' + str(page)

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=make_pager_url,
            item_count=query['count'],
            items_per_page=limit
        )

        c.page.items = query['results']
        return render('advanced_search/index.html')
