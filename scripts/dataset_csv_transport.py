#!/usr/bin/python3

import requests
import csv
import sys
from optparse import OptionParser

usage = "usage: %prog <CKAN_URL>"
parser = OptionParser(usage=usage)
parser.add_option("-e", "--export", dest="export_filename",
                  help="export data to FILE", metavar="FILE",
                  default='-')
parser.add_option("-i", "--import", dest="import_filename",
                  help="import data from FILE", metavar="FILE")
parser.add_option("-a", "--apikey", dest="apikey",
                  help="Use CKAN API key in requests")
parser.add_option("--ignore-errors", dest="ignore_errors", action="store_true",
                  help="Process entire CSV despite errors")

(opts, args) = parser.parse_args()
if len(args) != 1:
    parser.print_help()
    sys.exit(1)

CKAN_URL = args[0]


def action_url(action):
    return "%s/api/action/%s" % (CKAN_URL, action)


def json_get(url, headers={}):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Got error from API: %s", response.text)


def json_post(url, data={}, headers={}):
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    elif opts.ignore_errors:
        sys.stderr.write("\nGot error from API: %s\n" % response.text)
    else:
        raise Exception("Got error from API: %s", response.text)


def fetch_dataset_count(query=''):
    return json_get("%s?rows=0&q=%s" % (action_url('package_search'), query))['result']['count']


def fetch_datasets(query=''):
    page_size = 1000
    count = fetch_dataset_count(query)
    position = 0

    while position < count:
        datasets = json_get("%s?rows=%i&start=%i&q=%s" % (action_url('package_search'), page_size,
                                                          position, query))['result']['results']
        position += len(datasets)
        for dataset in datasets:
            yield dataset


def update_dataset(d):
    data = {
        'id': d['name'],
        'groups': [{'name': g.strip()} for g in d.get('groups', '').split(',')]
        }
    headers = {
            'X-CKAN-API-KEY': opts.apikey
            }

    json_post(action_url('package_patch'), headers=headers, data=data)


def export_datasets(filename):

    fields = ['name', 'title', 'url', 'groups', 'notes']
    f = sys.stdout if not filename or filename == '-' else open(filename, 'w')
    writer = csv.DictWriter(f, fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    sys.stderr.write('Fetching %i datasets\n' % fetch_dataset_count())
    datasets = fetch_datasets()
    for d in datasets:
        sys.stderr.write('  Fetching %s\r' % d['name'])
        values = {
                'name': d['name'],
                'title': d['title'],
                'notes': d['notes'],
                'url': '%s/dataset/%s' % (CKAN_URL, d['name']),
                'groups': ','.join(g['name'] for g in d.get('groups', []))
                }
        writer.writerow(values)


def import_datasets(filename):
    f = sys.stdin if filename == '-' else open(filename, 'r')
    reader = csv.DictReader(f)
    for row in reader:
        sys.stderr.write('Updating %s\r' % row['name'])
        update_dataset(row)


if opts.import_filename:
    import_datasets(opts.import_filename)
else:
    export_datasets(opts.export_filename)
