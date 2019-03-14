#!/usr/bin/python3

import requests
import json
import csv
import sys
from optparse import OptionParser

usage = "usage: %prog <CKAN_URL>"
parser = OptionParser(usage=usage)
(opts, args) = parser.parse_args()
if len(args) != 1:
    parser.print_help()
    sys.exit(1)

CKAN_URL = args[0]
PACKAGE_SEARCH_URL = "%s/api/action/package_search" % CKAN_URL
GA_VIEWS_URL = "%s/api/action/googleanalytics_dataset_visits" % CKAN_URL
SOLR_Q = "extras_collection_type:Interoperability+Tools"

def json_get(url, headers={}):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        raise Exception("Got error from API: %s", response.text)

datasets = json_get("%s?rows=1000&q=%s" % (PACKAGE_SEARCH_URL, SOLR_Q))['result']['results']

if len(datasets) == 1000:
    print("Exactly 1000 datasets received. This script needs to be fixed to handle paging.")
    sys.exit(1)

for dataset in datasets:
    dataset['views'] = json_get("%s?id=%s" % (GA_VIEWS_URL, dataset['name']))['result']['count']

fields = ['title', 'url', 'maintainer', 'maintainer_email', 'organization', 'content_type', 'author', 'author_email', 'created', 'modified', 'views']

writer = csv.DictWriter(sys.stdout, fields, quoting=csv.QUOTE_ALL)

writer.writeheader()
for dataset in datasets:
    values = {
            'title': dataset['title'],
            'url': '%s/dataset/%s' % (CKAN_URL, dataset['name']),
            'maintainer': dataset['maintainer'],
            'maintainer_email': dataset['maintainer_email'],
            'organization': dataset['organization']['title'],
            'content_type': ','.join(dataset['content_type']['fi']),
            'author': dataset['author'],
            'author_email': dataset['author_email'],
            'created': dataset['metadata_created'],
            'modified': dataset['metadata_modified'],
            'views': dataset['views']
            }
    writer.writerow(values)
