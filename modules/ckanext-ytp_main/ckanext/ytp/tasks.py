#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ckan import model, plugins
from ckan.lib import celery_app
from ckan.lib.cli import CkanCommand
from ckan.lib.munge import munge_title_to_name
from ckan.logic import get_action, NotFound, ValidationError
from contextlib import closing
from pylons import config
from rdflib import Graph, URIRef
from rdflib.namespace import SKOS, RDF
import json
import os
import re
import simplejson
import urllib2

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


def create_metadata_organization_and_dataset(meta_name, context):
    """Create an organization and a dataset to contain the preseeded tags."""

    values_organization = {'name': meta_name, 'id': meta_name}
    values_dataset = {
        'name': meta_name,
        'owner_org': meta_name,
        'license_id': ' ',
        'notes': ' ',
        'collection_type': ' ',
        'title': meta_name,
        'tag_string': ' ',
        'content_type': ' ',
    }

    get_action('organization_create')(context, values_organization)
    get_action('package_create')(context, values_dataset)


def parse_tag_list(data_url, data_format, tag_limit):
    """Parses a SKOS vocabulary file and forms a list of tag strings from the Finnish labels of each SKOS concept."""

    tag_list = []
    graph = Graph()
    graph.parse(data_url, format=data_format)

    for concept, concept_pred, concept_obj in graph.triples((None, RDF.type, SKOS.Concept)):
        for label, label_pred, label_obj in graph.triples((concept, SKOS.prefLabel, None)):
            if len(tag_list) < tag_limit:
                if label_obj.language == 'fi':
                    tag_list.append(unicode(cleanup_tag(label_obj)))
            else:
                break
    return tag_list


def cleanup_tag(unclean_tag):
    """CKAN is very nitpicky about tags: they can only have alphanumerics and special characters (- _ .)."""

    # Clean up parantheses nicely
    tag = re.sub('\)', '', unclean_tag)
    tag = re.sub('\(', '- ', tag)

    tag = re.sub(', ', ' ', tag)

    # Clean up everything else not so nicely
    tag = re.sub(u'[^0-9a-zA-ZöäåÖÄÅ\-\.\_\ ]+', u'_', tag)

    # Shorten very long tags
    tag = tag[:40]

    # print "cleaned up '%s' into '%s'" % (unclean_tag, tag)
    return tag


@celery_app.celery.task(name="ckanext.ytp.tags_import")
def tags_import(data):
    """ Imports tag vocabs into placeholder dataset """

    _load_config()
    context = _create_context()

    args = json.loads(data)
    max_number_of_tags = 40000

    # Attempt to create organization and dataset for the metadata.
    # This can fail gracefully if those already exist, but the
    # exception should be printed for other cases.
    # Unfortunately, these cases are indistinguishable in code
    # so we'll just print the exception in both
    try:
        create_metadata_organization_and_dataset(args['meta_name'], context)
    except ValidationError as e:
        print(repr(e))

    topic_tags = parse_tag_list(args['topic_url'], args['data_format'], max_number_of_tags)
    contenttype_tags = parse_tag_list(args['contenttype_url'], args['data_format'], max_number_of_tags)

    # Update tags of meta dataset
    get_action('package_update')(context, {'id': args['meta_name'],
                                           'tags': map((lambda tag: {'name': tag}), topic_tags),
                                           'content_type': reduce((lambda combined, next: combined + ',' + next), contenttype_tags),
                                           'license_id': ' ',
                                           'notes': ' ',
                                           'collection_type': ' ',
                                           'title': args['meta_name'],
                                           })

_config_loaded = False

@celery_app.celery.task(name="ckanext.ytp.organization_import")
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
                for key, value in item.iteritems():
                    values[key] = value
            values['id'] = values['name']

            if public_organization:
                values['public_adminstration_organization'] = 'true'
            try:
                get_action('organization_show')(context, {'id': values['id']})
                # Do not override organizations
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


@celery_app.celery.task(name="ckanext.ytp.organization_type_import")
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
