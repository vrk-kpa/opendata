#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This script downloads the Julkishallinnon ontologia JUHO ontology from
# the ontology library service ONKI.fi. JUHO ontology is licensed under
# Creative Commons Attribution 3.0 License
# http://creativecommons.org/licenses/by/3.0/legalcode


from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
import subprocess
import requests
import json
import re
import sys

YTP_META_ORG = 'ytp_metadata'
YTP_META_DATASET = 'ytp_metadata_tags'

# Create and organization to hide the metadata dataset
def create_metadata_organization(api_url_prefix, api_key):

  request_url = api_url_prefix + 'organization_create'
  request_payload = {
    'name': YTP_META_ORG
  }

  request_headers={
  'authorization': api_key,
  'content-type': 'application/json'
  }

  r = requests.post(request_url, data=json.dumps(request_payload), headers=request_headers)

  if r.status_code == 200:
    print "Organization created successfully"
  elif r.status_code == 409:
    print "Organization has already been created"
  else:
    print "Status code: %s" % r.status_code
    try:
      print json.dumps(r.json(), indent=2, sort_keys=True)
    except ValueError:
      print "Text: %s\n" % r.text

  return

# Create a dataset which will have all the preseeded tags as a workaround
def create_metadata_dataset(api_url_prefix, api_key):

  request_url = api_url_prefix + 'package_create'
  request_payload = {
    'name': YTP_META_DATASET,
    'owner_org': YTP_META_ORG,
    'notes': 'A dummy dataset that holds all the free tags users can add to datasets'
  }

  request_headers={
  'authorization': api_key,
  'content-type': 'application/json'
  }

  r = requests.post(request_url, data=json.dumps(request_payload), headers=request_headers)

  if r.status_code == 200:
    print "Dataset created successfully"
  elif r.status_code == 409:
    print "Dataset has already been created"
  else:
    print "Status code: %s" % r.status_code
    try:
      print json.dumps(r.json(), indent=2, sort_keys=True)
    except ValueError:
      print "Text: %s\n" % r.text

  return
  
# Parses an ontology file and forms a list of tag strings from the
# Finnish labels of each concept
def generate_tag_list_from_ontology(ontology_url, tag_limit):

  tag_list = []

  graph = Graph()
  print "Downloading and parsing ontology, this will take a while..."
  graph.parse(ontology_url, format='xml')

  LABEL_URI = URIRef(u'http://www.yso.fi/onto/yso-meta/2007-03-02/prefLabel')

  for subj, pred, obj in graph.triples((None, LABEL_URI, None)):
    if len(tag_list) < tag_limit:
      if obj.language=='fi':
        #tag_list.append(str(obj.encode('utf-8')))
        tag_list.append(unicode(obj))
    else:
      print "Reached tag limit of %s" % tag_limit
      break

  #for concept in g.triples((None, RDF.type, URIRef(u'http://www.yso.fi/onto/yso-meta/2007-03-02/Concept'))):
  #  print concept
  #  print g.preferredLabel(concept, lang='fi', labelProperties=(label_attribute))

  print "Parsed %s tags from %s triples" % (len(tag_list), len(graph))
  return tag_list


# CKAN is very nitpicky about tags: they can only have alphanumerics and
# special characters - _ .
def cleanup_tag(unclean_tag):

  # Clean up parantheses nicely
  tag = re.sub('\)', '', unclean_tag)
  tag = re.sub('\(', '- ', tag)

  tag = re.sub(', ', ' ', tag)
  
  # Clean up everything else not so nicely
  tag = re.sub(u'[^0-9a-zA-ZöäåÖÄÅ\-\.\_\ ]+', u'_', tag)

  # Shorten very long tags
  tag = tag[:40]

  #print "cleaned up '%s' into '%s'" % (unclean_tag, tag)
  return tag

# Update dataset with the tag list (replaces old tags)
def add_tags_to_ckan(tag_list, api_url_prefix, api_key):

  ckan_apified_tag_list = []
  
  for tag in tag_list:
    ckan_apified_tag_list.append({'name':cleanup_tag(tag)})

  request_url = api_url_prefix + 'package_update'
  request_payload = {
    'id': YTP_META_DATASET,
    'tags': ckan_apified_tag_list
  }

  request_headers={
  'authorization': api_key,
  'content-type': 'application/json'
  }

  r = requests.post(request_url, data=json.dumps(request_payload), headers=request_headers)

  if r.status_code == 200:
    print "Updated tags successfully"
  else:
    print "Status code: %s" % r.status_code
    try:
      print json.dumps(r.json(), indent=2, sort_keys=True)
    except ValueError:
      print "Text: %s\n" % r.text

  return


# Get CKAN API key for a sysadmin user
def get_api_key(user, ckan_env, ckan_config):
  
  p = subprocess.Popen([ckan_env + '/bin/paster',
    '--plugin=ckan', 
    'user', 
    user, 
    '--config=' + ckan_config], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  
  output, errors = p.communicate()
    
  api_key = output.split("apikey=",1)[1].split(" ",1)[0]
  return api_key


if __name__ == '__main__':

  # usage: parse-tags-from-ontology.py harvest /usr/lib/ckan/default /etc/ckan/default/production.ini

  if len(sys.argv) < 5:
    sys.exit('Error: Not enough arguments')

  api_username = sys.argv[1]
  ckan_env = sys.argv[2]
  ckan_config = sys.argv[3]
  ontology_url = sys.argv[4]
    
  api_url_prefix = 'http://localhost/data/api/3/action/'
  api_key = get_api_key(api_username, ckan_env, ckan_config)
  max_number_of_tags = 500

  create_metadata_organization(api_url_prefix, api_key)
  create_metadata_dataset(api_url_prefix, api_key)

  tags_to_add = generate_tag_list_from_ontology(ontology_url, max_number_of_tags)
  add_tags_to_ckan(tags_to_add, api_url_prefix, api_key)
  
