import logging
import urllib
import commands
import dbutil
import paste.deploy.converters as converters
import genshi
import pylons
import ckan.lib.helpers as h
import ckan.plugins as p
import gasnippet
from ckan.common import request
from ckan.lib import helpers

log = logging.getLogger('ckanext.googleanalytics')


class GoogleAnalyticsException(Exception):
    pass


class GoogleAnalyticsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IGenshiStreamFilter, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers)

    def configure(self, config):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        if 'googleanalytics.id' not in config:
            msg = "Missing googleanalytics.id in config"
            raise GoogleAnalyticsException(msg)
        self.googleanalytics_id = config['googleanalytics.id']
        self.googleanalytics_domain = config.get(
                'googleanalytics.domain', 'auto')
        self.googleanalytics_javascript_url = h.url_for_static(
                '/scripts/ckanext-googleanalytics.js')
        self.googleanalytics_type = config.get('googleanalytics.type', 'classic')

        if self.googleanalytics_type == 'universal':
            self.analytics_html = 'googleanalytics/snippets/googleanalytics_header_ua.html'
            self.analytics_js = 'ckanext-googleanalytics/googleanalytics_event_tracking_ua.js'
        elif self.googleanalytics_type == 'classic':
            self.analytics_html = 'googleanalytics/snippets/googleanalytics_header.html'
            self.analytics_js = 'ckanext-googleanalytics/googleanalytics_event_tracking.js'
        else:
            raise GoogleAnalyticsException("Invalid 'googleanalytics.type' value '%s'. Should be "
                                           "'classic' or 'universal'." % self.googleanalytics_type)

        # If resource_prefix is not in config file then write the default value
        # to the config dict, otherwise templates seem to get 'true' when they
        # try to read resource_prefix from config.
        if 'googleanalytics_resource_prefix' not in config:
            config['googleanalytics_resource_prefix'] = (
                    commands.DEFAULT_RESOURCE_URL_TAG)
        self.googleanalytics_resource_prefix = config[
            'googleanalytics_resource_prefix']

        self.show_downloads = converters.asbool(
            config.get('googleanalytics.show_downloads', True))
        self.track_events = converters.asbool(
            config.get('googleanalytics.track_events', False))

        if not converters.asbool(config.get('ckan.legacy_templates', 'false')):
            p.toolkit.add_resource('fanstatic_library', 'ckanext-googleanalytics')

    def update_config(self, config):
        '''Change the CKAN (Pylons) environment configuration.

        See IConfigurer.

        '''
        if converters.asbool(config.get('ckan.legacy_templates', 'false')):
            p.toolkit.add_template_directory(config, 'legacy_templates')
            p.toolkit.add_public_directory(config, 'legacy_public')
        else:
            p.toolkit.add_template_directory(config, 'templates')

    def after_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        map.redirect("/analytics/package/top", "/analytics/dataset/top")
        map.connect(
            'analytics', '/analytics/dataset/top',
            controller='ckanext.googleanalytics.controller:GAController',
            action='view'
        )
        return map

    def filter(self, stream):
        '''Insert Google Analytics code into legacy Genshi templates.

        This is called by CKAN whenever any page is rendered, _if_ using old
        CKAN 1.x legacy templates. If using new CKAN 2.0 Jinja templates, the
        template helper methods below are used instead.

        See IGenshiStreamFilter.

        '''
        log.info("Inserting Google Analytics code into template")

        # Add the Google Analytics tracking code into the page header.
        header_code = genshi.HTML(gasnippet.header_code
            % (self.googleanalytics_id, self.googleanalytics_domain))
        stream = stream | genshi.filters.Transformer('head').append(
                header_code)

        # Add the Google Analytics Event Tracking script into the page footer.
        if self.track_events:
            footer_code = genshi.HTML(
                gasnippet.footer_code % self.googleanalytics_javascript_url)
            stream = stream | genshi.filters.Transformer(
                    'body/div[@id="scripts"]').append(footer_code)

        routes = pylons.request.environ.get('pylons.routes_dict')
        action = routes.get('action')
        controller = routes.get('controller')

        if ((controller == 'package' and
             action in ['search', 'read', 'resource_read']) or
            (controller == 'group' and action == 'read')):

            log.info("Tracking of resource downloads")

            # add download tracking link
            def js_attr(name, event):
                attrs = event[1][1]
                href = attrs.get('href').encode('utf-8')
                link = '%s%s' % (self.googleanalytics_resource_prefix,
                                 urllib.quote(href))
                js = "javascript: _gaq.push(['_trackPageview', '%s']);" % link
                return js

            # add some stats
            def download_adder(stream):
                download_html = '''<span class="downloads-count">
                [downloaded %s times]</span>'''
                count = None
                for mark, (kind, data, pos) in stream:
                    if mark and kind == genshi.core.START:
                        href = data[1].get('href')
                        if href:
                            count = dbutil.get_resource_visits_for_url(href)
                    if count and mark is genshi.filters.transform.EXIT:
                        # emit count
                        yield genshi.filters.transform.INSIDE, (
                            genshi.core.TEXT,
                            genshi.HTML(download_html % count), pos)
                    yield mark, (kind, data, pos)

            # perform the stream transform
            stream = stream | genshi.filters.Transformer(
                '//a[contains(@class, "resource-url-analytics")]').attr(
                    'onclick', js_attr)

            if (self.show_downloads and action == 'read' and
                controller == 'package'):
                stream = stream | genshi.filters.Transformer(
                    '//a[contains(@class, "resource-url-analytics")]').apply(
                        download_adder)
                stream = stream | genshi.filters.Transformer('//head').append(
                    genshi.HTML(gasnippet.download_style))

        return stream

    def get_helpers(self):
        '''Return the CKAN 2.0 template helper functions this plugin provides.

        See ITemplateHelpers.

        '''
        return {'googleanalytics_header': self.googleanalytics_header,
                'googleanalytics_event_tracking': self.googleanalytics_event_tracking}

    def googleanalytics_event_tracking(self):
        '''Return correct event tracking resource for CKAN 2.0 templates.'''
        return self.analytics_js

    def googleanalytics_header(self):
        '''Render the googleanalytics_header snippet for CKAN 2.0 templates.

        This is a template helper function that renders the
        googleanalytics_header jinja snippet. To be called from the jinja
        templates in this extension, see ITemplateHelpers.

        '''

        domain = self.googleanalytics_domain if self.googleanalytics_domain != 'request' else request.environ['HTTP_HOST']
        data = {'googleanalytics_id': self.googleanalytics_id,
                'googleanalytics_domain': domain}

        return p.toolkit.render_snippet(self.analytics_html, data)
