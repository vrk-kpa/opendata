import urllib2
import simplejson
import os
from contextlib import closing

from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

from ckan import model, plugins
from ckan.logic import get_action, NotFound
from ckan.lib import celery_app
from ckan.lib.munge import munge_title_to_name
from ckan.lib.cli import CkanCommand

_config_loaded = False


class FakeOptions():
    """ Fake options for fake command """
    config = os.environ.get('CKAN_CONFIG')


def _load_config():
    # We want CKAN environment loaded. Here we fake that this is a CKAN command.
    global _config_loaded
    if _config_loaded:
        return
    _config_loaded = True

    command = CkanCommand(None)
    command.options = FakeOptions()
    command._load_config()


def _create_context():
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
    context['user'] = admin_user['name']
    return context


@celery_app.celery.task(name="ckanext.ytp.organizations.organization_import")
def organization_import(data):
    """ Import organizations """
    _load_config()
    context = _create_context()
    configuration = simplejson.loads(data)
    data_url = configuration.get('url')
    public_organization = configuration.get('public_organization', False)

    with closing(urllib2.urlopen(data_url)) as source:
        data = simplejson.load(source)

        for item in data:
            if isinstance(item, basestring):
                title = item.strip()
                name = munge_title_to_name(title).lower()
            else:
                title = item['title']
                name = item['name']
            values = {'name': name, 'title': title, 'id': name}
            if public_organization:
                values['extras'] = [{'key': 'public_adminstration_organization', 'value': 'true'}]
            try:
                organization = get_action('organization_show')(context, values)
                if organization['title'] != title:
                    organization = get_action('organization_update')(context, values)
            except NotFound:
                organization = get_action('organization_create')(context, values)


def _add_children_concepts(graph, current, prefix='', indent=0, max_depth=8, data=None):
    """ Add a SKOS concept and its children recursively into a pseudo-hierarchical data """
    sister = 0
    if data is None:
        data = []
        data.append({'name': prefix + " " + graph.value(current, SKOS.prefLabel)})

    if indent < max_depth:
        for _subject, _predicate, child in graph.triples((current, SKOS.narrower, None)):
            sister += 1
            data.append({'name': prefix + '.' + str(sister) + " " + graph.value(child, SKOS.prefLabel)})
            _add_children_concepts(graph, child, prefix + '.' + str(sister), indent + 1, max_depth, data)

        for _subject, _predicate, child in graph.triples((current, SKOS.member, None)):
            sister += 1
            data.append({'name': prefix + str(sister) + " " + graph.value(child, SKOS.prefLabel)})
            _add_children_concepts(graph, child, prefix + str(sister), indent + 1, max_depth, data)

    return data


@celery_app.celery.task(name="ckanext.ytp.organizations.organization_type_import")
def organization_type_import(data):
    """ Import organization types """

    _load_config()
    context = _create_context()

    data_url = simplejson.loads(data).get('data_url')
    data_format = simplejson.loads(data).get('data_format')

    graph = Graph()
    graph.parse(data_url, format=data_format)

    services = (('private_services', 'http://www.yso.fi/onto/jupo/p728', "1"), ('public_services', 'http://www.yso.fi/onto/jupo/p605', "2"))

    for service_name, service_url, prefix in services:
        organization_types = _add_children_concepts(graph, URIRef(service_url), prefix)

        try:
            get_action('vocabulary_show')(context, {'id': service_name})
            for tag in get_action('tag_list')(context, {'vocabulary_id': service_name, 'query': None, 'all_fields': True}):
                get_action('tag_delete')(context, {'id': tag['id']})

            get_action('vocabulary_delete')(context, {'id': service_name})
        except NotFound:
            pass  # Vocabulary does not exist
        get_action('vocabulary_create')(context, {'name': service_name, 'tags': organization_types})
