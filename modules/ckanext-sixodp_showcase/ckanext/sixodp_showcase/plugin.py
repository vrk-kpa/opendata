import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.showcase.plugin import ShowcasePlugin
import ckanext.showcase.logic.helpers as showcase_helpers
from ckanext.showcase.logic import action as showcase_action
from logic.action import create, update, get
from ckanext.sixodp_showcase import helpers
from ckan.common import _
from ckan.lib import i18n
import json

import ckan.lib.helpers as h

from routes.mapper import SubMapper

try:
    from collections import OrderedDict  # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

import logging
log = logging.getLogger(__name__)


class Sixodp_ShowcasePlugin(ShowcasePlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'sixodp_showcase')

    # IDatasetForm

    def package_types(self):
        return []

    def search_template(self):
        return "sixodp_showcase/search.html"

    def read_template(self):
        return "sixodp_showcase/read.html"

    def edit_template(self):
        return 'sixodp_showcase/edit.html'

    def before_map(self, map):

        with SubMapper(map, controller='ckanext.sixodp_showcase.controller:Sixodp_ShowcaseController') as m:
            m.connect('ckanext_showcase_new', '/showcase/new', action='new')
            m.connect('ckanext_showcase_edit', '/showcase/edit/{id}',
                      action='edit', ckan_icon='edit')
            m.connect('ckanext_showcase_index', '/showcase', action='search',
                      highlight_actions='index search')
            m.connect('ckanext_showcase_admins', '/ckan-admin/showcase_admins',
                      action='manage_showcase_admins', ckan_icon='picture'),
            m.connect('ckanext_showcase_delete', '/showcase/delete/{id}',
                      action='delete')

        with SubMapper(map, controller='ckanext.showcase.controller:ShowcaseController') as m:
            m.connect('ckanext_showcase_manage_datasets',
                      '/showcase/manage_datasets/{id}',
                      action="manage_datasets", ckan_icon="sitemap")
            m.connect('dataset_showcase_list', '/dataset/showcases/{id}',
                      action='dataset_showcase_list', ckan_icon='picture')
            # m.connect('ckanext_showcase_admins', '/ckan-admin/showcase_admins',
            #          action='manage_showcase_admins', ckan_icon='picture'),
            m.connect('ckanext_showcase_admin_remove',
                      '/ckan-admin/showcase_admin_remove',
                      action='remove_showcase_admin')
        map.redirect('/showcases', '/showcase')
        map.redirect('/showcases/{url:.*}', '/showcase/{url}')

        return map

    # IFacets #

    _LOCALE_ALIASES = {'en_GB': 'en'}

    def dataset_facets(self, facets_dict, package_type):
        if(package_type == 'showcase'):
            facets_dict = OrderedDict()

            lang = i18n.get_lang()

            if lang in self._LOCALE_ALIASES:
                lang = self._LOCALE_ALIASES[lang]

            facets_dict.update({'groups': _('Groups')})
            facets_dict['vocab_keywords_' + lang] = _('Tags')

            facets_dict.update({'vocab_platform': _('Platforms')})

        return facets_dict

    # IRoutes

    def get_actions(self):
        action_functions = {
            'ckanext_showcase_create':
                create.showcase_create,
            'ckanext_showcase_update':
                update.showcase_update,
            'ckanext_showcase_delete':
                showcase_action.delete.showcase_delete,
            'ckanext_showcase_show':
                showcase_action.get.showcase_show,
            'ckanext_showcase_list':
                get.showcase_list,
            'ckanext_showcase_package_association_create':
                showcase_action.create.showcase_package_association_create,
            'ckanext_showcase_package_association_delete':
                showcase_action.delete.showcase_package_association_delete,
            'ckanext_showcase_package_list':
                showcase_action.get.showcase_package_list,
            'ckanext_package_showcase_list':
                get.package_showcase_list,
            'ckanext_showcase_admin_add':
                showcase_action.create.showcase_admin_add,
            'ckanext_showcase_admin_remove':
                showcase_action.delete.showcase_admin_remove,
            'ckanext_showcase_admin_list':
                showcase_action.get.showcase_admin_list,
        }
        return action_functions

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'facet_remove_field': showcase_helpers.facet_remove_field,
            'get_site_statistics': showcase_helpers.get_site_statistics,
            'get_featured_showcases': helpers.get_featured_showcases,
            'get_showcases_by_author': helpers.get_showcases_by_author,
            'get_vocabulary': helpers.get_vocabulary,
            'translate_list_items': helpers.translate_list_items,
            'get_showcase_pkgs': helpers.get_showcase_pkgs
        }

    def _add_image_urls(self, pkg_dict):

        # Add a image urls for the Showcase image to the pkg dict so template
        # has access to it.

        imgs = ['icon', 'featured_image', 'image_1', 'image_2', 'image_3']
        for image in imgs:
            image_url = pkg_dict.get(image)
            pkg_dict[image + '_display_url'] = image_url
            if image_url and not image_url.startswith('http'):
                pkg_dict[image] = image_url
                pkg_dict[image + '_display_url'] = \
                    h.url_for_static('uploads/{0}/{1}'.format('showcase',
                                                              pkg_dict.get(image)),
                                     qualified=True)

    def _add_to_pkg_dict(self, context, pkg_dict):
        '''
        Add key/values to pkg_dict and return it.
        '''

        if pkg_dict['type'] != 'showcase':
            return pkg_dict

        self._add_image_urls(pkg_dict)

        # Add dataset count
        pkg_dict[u'num_datasets'] = len(
            toolkit.get_action('ckanext_showcase_package_list')(
                context, {'showcase_id': pkg_dict['id']}))

        # Rendered notes
        pkg_dict[u'showcase_notes_formatted'] = \
            h.render_markdown(pkg_dict['notes'])
        return pkg_dict

    # IPackageController
    def after_show(self, context, data_dict):
        if context.get('for_edit') is not True:
            if data_dict.get('notifier', None) is not None:
                data_dict.pop('notifier')
            if data_dict.get('notifier_email', None) is not None:
                data_dict.pop('notifier_email')

        return self._add_to_pkg_dict(context, data_dict)

    def before_index(self, data_dict):
        if data_dict.get('platform'):
            data_dict['vocab_platform'] = [tag for tag in data_dict['platform'].split(',')]

        vocabs = ['keywords']
        languages = ['fi', 'sv', 'en']

        for prop_key in vocabs:
            prop_json = data_dict.get(prop_key)
            if not prop_json:
                continue
            prop_value = json.loads(prop_json)
            for lang in languages:
                lang_values = prop_value.get(lang)
                if lang_values:
                    data_dict['vocab_%s_%s' % (prop_key, lang)] = list(lang_values)

        return data_dict

    def after_search(self, search_results, search_params):
        if(search_results['search_facets'].get('groups')):
            context = {'for_view': True, 'with_private': False}
            data_dict = {
                'all_fields': True,
                'include_extras': True,
                'type': 'group',
            }
            groups_with_extras = toolkit.get_action('group_list')(context, data_dict)

            for i, facet in enumerate(search_results['search_facets']['groups'].get('items', [])):
                for group in groups_with_extras:
                    if facet['name'] == group['name']:
                        search_results['search_facets']['groups']['items'][i]['title_translated'] = \
                            group.get('title_translated')

        for result in search_results['results']:
            self._add_image_urls(result)

        return search_results
