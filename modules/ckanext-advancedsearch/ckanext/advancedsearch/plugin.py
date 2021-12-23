#!/usr/bin/env python
# encoding: utf-8

import inspect
import logging
import os
import sys

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.advancedsearch import action, controller, helpers, loader

from paste.reloader import watch_file

log = logging.getLogger(__name__)


class AdvancedsearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.ITranslation)

    @classmethod
    def _store_instance(cls, self):
        AdvancedsearchPlugin.instance = self

    # IConfigurer
    def update_config(self, config):
        # record our plugin instance in a place where our helpers
        # can find it:
        self._store_instance(self)

        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'advancedsearch')

        self._schema = _load_schema(config.get('advancedsearch.schema', ""))

    # IActions
    def get_actions(self):
        return {
            'get_formats': action.get_formats,
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'field_options': helpers.field_options,
            'advancedsearch_schema': helpers.advancedsearch_schema,
            'advanced_category_options': helpers.advanced_category_options,
            'advanced_publisher_options': helpers.advanced_publisher_options,
            'advanced_license_options': helpers.advanced_license_options,
            'advanced_format_options': helpers.advanced_format_options,
            'advanced_multiselect_query': helpers.advanced_multiselect_query,
            'advanced_search_and_target_query': helpers.advanced_search_and_target_query,
            'advanced_search_query': helpers.advanced_search_query,
            'advanced_daterange_query': helpers.advanced_daterange_query,
            'query_helper': helpers.query_helper,
            'value_or_blank': helpers.value_or_blank,
            'selected_index_radio': helpers.selected_index_radio,
            'selected_indexes_checkboxes': helpers.selected_indexes_checkboxes,
            'advanced_dataset_types_options': helpers.advanced_dataset_types_options
        }

    # IBlueprint
    def get_blueprint(self):
        return controller.get_blueprints()

    # ITranslator

    # The following methods are copied from ckan.lib.plugins.DefaultTranslation
    # and have been modified to fix a bug in CKAN 2.5.1 that prevents CKAN from
    # starting. In addition by copying these methods, it is ensured that Data
    # Requests can be used even if Itranslation isn't available (less than 2.5)

    def i18n_directory(self):
        '''Change the directory of the *.mo translation files
        The default implementation assumes the plugin is
        ckanext/myplugin/plugin.py and the translations are stored in
        i18n/
        '''
        # assume plugin is called ckanext.<myplugin>.<...>.PluginClass
        extension_module_name = '.'.join(self.__module__.split('.')[:3])
        module = sys.modules[extension_module_name]
        return os.path.join(os.path.dirname(module.__file__), 'i18n')

    def i18n_locales(self):
        '''Change the list of locales that this plugin handles
        By default the will assume any directory in subdirectory in the
        directory defined by self.directory() is a locale handled by this
        plugin
        '''
        directory = self.i18n_directory()
        return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    def i18n_domain(self):
        '''Change the gettext domain handled by this plugin
        This implementation assumes the gettext domain is
        ckanext-{extension name}, hence your pot, po and mo files should be
        named ckanext-{extension name}.mo'''
        return 'ckanext-{name}'.format(name=self.name)


def _load_schema(url):
    schema = _load_schema_module_path(url)
    if not schema:
        schema = _load_schema_url(url)
    return schema


def _load_schema_module_path(url):
    """
    Given a path like "ckanext.spatialx:spatialx_schema.json"
    find the second part relative to the import path of the first
    """

    module, file_name = url.split(':', 1)
    try:
        # __import__ has an odd signature
        m = __import__(module, fromlist=[''])
    except ImportError:
        return
    p = os.path.join(os.path.dirname(inspect.getfile(m)), file_name)
    if os.path.exists(p):
        watch_file(p)
        return loader.load(open(p))


def _load_schema_url(url):
    import urllib2
    try:
        res = urllib2.urlopen(url)
        tables = res.read()
    except urllib2.URLError:
        raise Exception("Could not load %s" % url)

    return loader.loads(tables, url)
