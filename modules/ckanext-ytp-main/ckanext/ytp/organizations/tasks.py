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

from pylons import config

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
            values = {}
            if isinstance(item, basestring):
                values['title'] = item.strip()
                values['name'] = munge_title_to_name(values['title']).lower()
            else:
                values['name'] = item.pop('name')
                values['title'] = item.pop('title')
                values['description'] = item.pop('description', None)
                values['extras'] = [{'key': key, 'value': value} for key, value in item.iteritems()]
            values['id'] = values['name']

            if public_organization:
                values['extras'] = [{'key': 'public_adminstration_organization', 'value': 'true'}]
            try:
                get_action('organization_update')(context, values)
            except NotFound:
                get_action('organization_create')(context, values)


def _add_child_concepts(graph, current_uri, depth=0, max_depth=8):
    """ Add a SKOS concept and its children recursively into a pseudo-hierarchical data """

    branch = {'text': graph.value(current_uri, SKOS.prefLabel), 'state': {'opened': True}}

    if depth < max_depth:
        for _subject, _predicate, child in graph.triples((current_uri, SKOS.narrower, None)):
            if 'children' not in branch:
                branch['children'] = []
            branch['children'].append(_add_child_concepts(graph, child, depth + 1, max_depth))
    return branch


def _dump_json(path, data):
    if path.startswith("file://"):
        path = path[7:]
    with open(path, 'w') as json_file:
        json_file.write(simplejson.dumps(data, indent=2))


@celery_app.celery.task(name="ckanext.ytp.organizations.organization_type_import")
def organization_type_import(data):
    """ Import organization types """

    _load_config()

    data_url = simplejson.loads(data).get('data_url')
    data_format = simplejson.loads(data).get('data_format')

    graph = Graph()
    graph.parse(data_url, format=data_format)

    private_url = 'http://www.yso.fi/onto/jupo/p728'
    public_url = 'http://www.yso.fi/onto/jupo/p605'

    _dump_json(config.get("producer_type_private_options_url"), [_add_child_concepts(graph, URIRef(private_url))])
    _dump_json(config.get("producer_type_options_url"), [_add_child_concepts(graph, URIRef(top_type)) for top_type in (private_url, public_url)])
