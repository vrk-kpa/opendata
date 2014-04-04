#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This script parses Excel spreadsheets into RDF/SKOS vocabularies."""

import logging
import sys
import pandas
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, DC, DCTERMS

logging.basicConfig()

uri_prefix = "http://avoindata.fi/onto/"
uri_common_part = "/p"


def convert_spreadsheet_into_vocabularies(filename):
    """Parse Excel spreadsheet and create SKOS vocabularies from each sheet."""

    vocabs = [
        {'sheet': 'AIHE', 'vocabulary_name': 'topic', 'metadata_sheet': 'AIHE_meta'},
        {'sheet': u'SISÄLTÖTYYPPI', 'vocabulary_name': 'contentType', 'metadata_sheet': u'SISÄLTÖTYYPPI_meta'},
    ]

    for vocab in vocabs:

        graph = Graph()
        graph.bind('skos', SKOS)
        graph.bind('rdfs', RDFS)
        graph.bind('dc11', DC)
        graph.bind('dct', DCTERMS)
        graph.bind('yso', URIRef('http://www.yso.fi/onto/yso'))

        parse_concepts_from_sheet(graph, vocab['vocabulary_name'], pandas.read_excel(filename, vocab['sheet'], index_col='ID'))
        parse_metadata_from_sheet(graph, vocab['vocabulary_name'], pandas.read_excel(filename, vocab['metadata_sheet']))
        serialize_vocab_into_file(graph, vocab['vocabulary_name'])

    return


def parse_concepts_from_sheet(graph, vocabulary_name, sheet_data):
    """Parse vocabulary concepts from spreadsheet and into a graph."""

    base_uri = uri_prefix + vocabulary_name

    for index, row in sheet_data.iterrows():

        concept = URIRef(base_uri + uri_common_part + str(index))
        graph.add((concept, RDF.type, SKOS.Concept))
        graph.add((concept, SKOS.inScheme, URIRef(base_uri)))

        graph.add((concept, SKOS.topConceptOf, URIRef(base_uri)))
        graph.add((URIRef(base_uri), SKOS.hasTopConcept, concept))

        graph.add((concept, SKOS.prefLabel, Literal(row['Suomeksi'].rstrip(), lang='fi')))
        graph.add((concept, SKOS.prefLabel, Literal(row['Englanniksi'].rstrip(), lang='en')))
        graph.add((concept, SKOS.prefLabel, Literal(row['Ruotsiksi'].rstrip(), lang='sv')))

        if pandas.notnull(row[u'Synonyymi (YSO)']):
            graph.add((concept, SKOS.exactMatch, URIRef(str(row['Synonyymi (YSO)']))))

        if pandas.notnull(row[u'Läheinen käsite']):
            graph.add((concept, SKOS.closeMatch, URIRef(str(row[u'Läheinen käsite']))))

    return


def parse_metadata_from_sheet(graph, vocabulary_name, sheet_data):
    """Parse metadata regarding the SKOS vocabulary itself from a spreadsheet and into a graph."""

    base_uri = uri_prefix + vocabulary_name

    concept_scheme = URIRef(base_uri)
    graph.add((concept_scheme, RDF.type, SKOS.ConceptScheme))

    meta_to_triples(graph, concept_scheme, DC.publisher, 'Publisher', sheet_data)
    meta_to_triples(graph, concept_scheme, DC.title, 'Title/label', sheet_data)
    meta_to_triples(graph, concept_scheme, SKOS.prefLabel, 'Title/label', sheet_data)
    meta_to_triples(graph, concept_scheme, DC.description, 'Description', sheet_data)
    graph.add((concept_scheme, DCTERMS.license, URIRef(str(sheet_data.ix['License', 'SUOMI']))))

    return


def meta_to_triples(graph, subject, predicate, metafield, sheet_data):
    """Convert multilingual metadata fields into triples. This trims trailing whitespace from labels."""

    # Known issue: this does not handle correctly cells that have only whitespace in them
    if pandas.notnull(sheet_data.ix[metafield, 'SUOMI']):
        graph.add((subject, predicate, Literal(sheet_data.ix[metafield, 'SUOMI'].rstrip(), lang='fi')))
    if pandas.notnull(sheet_data.ix[metafield, 'ENGLANTI']):
        graph.add((subject, predicate, Literal(sheet_data.ix[metafield, 'ENGLANTI'].rstrip(), lang='en')))
    if pandas.notnull(sheet_data.ix[metafield, 'RUOTSI']):
        graph.add((subject, predicate, Literal(sheet_data.ix[metafield, 'RUOTSI'].rstrip(), lang='sv')))

    return


def serialize_vocab_into_file(graph, vocabulary_name):
    """Serialize vocabulary as RDF/XML into a file."""

    filename = 'avoindatafi_' + vocabulary_name + '.rdf'
    graph.serialize(filename, format='pretty-xml')
    print "Wrote file", filename

    return


if __name__ == "__main__":
    # Must get xlsx filename as arg
    assert len(sys.argv) == 2
    convert_spreadsheet_into_vocabularies(sys.argv[1])
