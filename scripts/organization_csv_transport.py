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


def fetch_organization(id_or_name):
    sys.stderr.write('  Fetching %s\r' % id_or_name)
    return json_get('%s?id=%s' % (action_url('organization_show'), id_or_name))['result']


def fetch_organizations():
    sys.stderr.write('Fetching organization names\n')
    names = json_get(action_url('organization_list'))['result']
    sys.stderr.write('Fetching %i organizations\n' % len(names))
    return [fetch_organization(name) for name in names]


def update_organization(o):
    data = {
        'id': o['name'],
        'producer_type': o['producer_type']
        }
    headers = {
            'X-CKAN-API-KEY': opts.apikey
            }

    json_post(action_url('organization_patch'), headers=headers, data=data)


def export_organizations(filename):
    organizations = fetch_organizations()

    fields = ['name', 'title', 'description', 'url', 'producer_type']
    f = sys.stdout if not filename or filename == '-' else open(filename, 'w')
    writer = csv.DictWriter(f, fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for o in organizations:
        values = {
                'name': o['name'],
                'title': o['title'],
                'description': o['description'],
                'url': '%s/organization/%s' % (CKAN_URL, o['name']),
                'producer_type': o.get('producer_type', ''),
                }
        writer.writerow(values)


def import_organizations(filename):
    f = sys.stdin if filename == '-' else open(filename, 'r')
    reader = csv.DictReader(f)
    for row in reader:
        sys.stderr.write('Updating %s\r' % row['name'])
        update_organization(row)


if opts.import_filename:
    import_organizations(opts.import_filename)
else:
    export_organizations(opts.export_filename)
