#!/usr/bin/env python
# encoding: utf-8

import os
import inspect
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from paste.reloader import watch_file

from ckanext.advancedsearch import loader
from ckanext.advancedsearch import helpers
from ckanext.advancedsearch import action

log = logging.getLogger(__name__)


class AdvancedsearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)

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

        log.info(config.get('advancedsearch.schema', ""))
        self._schema = _load_schema(config.get('advancedsearch.schema', ""))

    def get_actions(self):
        return {'get_organizations': action.get_organizations}

    def get_helpers(self):
        return {
            'field_options': helpers.field_options,
            'advancedsearch_schema': helpers.advancedsearch_schema,
            'category_options': helpers.category_options,
            'publisher_options': helpers.publisher_options,
            'license_options': helpers.license_options,
            'format_options': helpers.format_options,
        }

    def before_map(self, m):
        m.connect(
            '/advanced_search',
            action='search',
            controller='ckanext.advancedsearch.controller:YtpAdvancedSearchController'
        )
        return m


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
