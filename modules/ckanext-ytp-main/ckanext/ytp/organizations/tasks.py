import urllib2
import simplejson
import os
from contextlib import closing

from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

from ckan import model, plugins
from ckan.logic import get_action, NotFound, ValidationError
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

    data_url = simplejson.loads(data).get('url')

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
            try:
                organization = get_action('organization_show')(context, values)
                if organization['title'] != title:
                    organization = get_action('organization_update')(context, values)
            except NotFound:
                organization = get_action('organization_create')(context, values)


def _user_has_organization(username):
    user = model.User.get(username)
    if not user:
        raise NotFound("Failed to find user")
    query = model.Session.query(model.Member).filter(model.Member.table_name == 'user').filter(model.Member.table_id == user.id)
    return query.count() > 0


def _create_default_organization(context, organization_name, organization_title):
    values = {'name': organization_name, 'title': organization_title, 'id': organization_name}
    try:
        return plugins.toolkit.get_action('organization_show')(context, values)
    except NotFound:
        return plugins.toolkit.get_action('organization_create')(context, values)


@celery_app.celery.task(name="ckanext.ytp.organizations.default_organization")
def default_organization(username, organization_name, organization_title):
    _load_config()
    if _user_has_organization(username):
        return
    context = _create_context()
    organization = _create_default_organization(context, organization_name, organization_title)
    plugins.toolkit.get_action('organization_member_create')(context, {"id": organization['id'], "username": username, "role": "editor"})


def _add_children_concepts(list, graph, current, indent, max_depth, prefix):
    """ Add a SKOS concept and its children recursively into a pseudo-hierarchical list """

    sister = 0

    if indent < max_depth:
        for subj, pred, child in graph.triples((current, SKOS.narrower, None)):
            sister += 1
            list.append({'name': prefix + '.' + str(sister) + " " + graph.value(child, SKOS.prefLabel)})
            _add_children_concepts(list, graph, child, indent + 1, max_depth, prefix + '.' + str(sister))

    # Top-level items
    if indent < max_depth:
        for subj, pred, child in graph.triples((current, SKOS.member, None)):
            sister += 1
            list.append({'name': prefix + str(sister) + " " + graph.value(child, SKOS.prefLabel)})
            _add_children_concepts(list, graph, child, indent + 1, max_depth, prefix + str(sister))

    return


@celery_app.celery.task(name="ckanext.ytp.organizations.organization_type_import")
def organization_type_import(data):
    """ Import organization types """

    _load_config()
    context = _create_context()

    data_url = simplejson.loads(data).get('data_url')
    data_format = simplejson.loads(data).get('data_format')

    graph = Graph()
    graph.parse(data_url, format=data_format)

    vocabulary_name = 'ytp_organization_types'
    org_types = []

    _add_children_concepts(org_types, graph, URIRef('http://www.yso.fi/onto/jupo/p1050'), 0, 8, '')

    try:
        get_action('vocabulary_create')(context, {'name': vocabulary_name, 'tags': org_types})
    except ValidationError:
        existing_vocab = get_action('vocabulary_show')(context, {'id': vocabulary_name})
        existing_id = existing_vocab.get('id')
        get_action('vocabulary_update')(context, {'id': existing_id, 'tags': org_types})
