#!/usr/bin/python3

import requests
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
        return response.json()
    else:
        raise Exception("Got error from API: %s", response.text)

def fetch_datasets(query):
    page_size = 1000
    count = json_get("%s?rows=0&q=%s" % (PACKAGE_SEARCH_URL, query))['result']['count']
    position = 0

    while position < count:
        datasets = json_get("%s?rows=%i&start=%i&q=%s" % (PACKAGE_SEARCH_URL, page_size, position, query))['result']['results']
        position += len(datasets)
        for dataset in datasets:
            yield dataset

datasets = list(fetch_datasets(SOLR_Q))

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
