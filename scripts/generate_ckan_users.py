#!/usr/bin/env python
#

'''
Generates deterministically random users into an organization as bulk process
'''

import ckanapi
import datetime
import argparse
import random
import re
import logging

logging.basicConfig(format='%(message)s')


def name_generator():
    words = [x.strip() for x in open('/usr/share/dict/words', 'r') if re.match('^[A-Za-z]*$', x)]
    while True:
        yield '-'.join([random.choice(words) for i in range(3)]).lower()


def create_user(api, name, organization=None):
    print('Creating user %s' % (name))
    api.action.user_create(**{
        'name': name,
        'email': '%s@doesnot.exist' % name,
        'password': 'password-for-%s' % name
    })
    if organization:
        print('Joining user %s to organization %s' % (name, organization))
        api.action.member_create(**{
            'id': organization,
            'object': name,
            'object_type': 'user',
            'capacity': 'member'
        })


def main():
    parser = argparse.ArgumentParser(description='Generates CKAN datasets')
    parser.add_argument('-b', '--base', default='http://localhost:5000',
                        help='Base URL for CKAN API to post to [default: \'%(default)s\']')
    parser.add_argument('-a', '--apikey', default='tester',
                        help='API key to post with [default: \'%(default)s\']')
    parser.add_argument('-s', '--seed', default=0, type=int,
                        help='Random seed for user name generation [default: %(default)s]')
    parser.add_argument('-o', '--organization', default=None,
                        help='Join created users to organization')
    parser.add_argument('num_users', metavar='N', type=int,
                        help='Number of users')
    args = parser.parse_args()

    user_agent_ident = 'generate_ckan_users-{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.utcnow())

    api = ckanapi.RemoteCKAN(args.base,
                             apikey=args.apikey,
                             user_agent='avoindata_ckanapi_users/1.0 ({0})'.format(user_agent_ident))

    num_users = args.num_users
    organization = args.organization

    random.seed(args.seed)
    names = name_generator()

    try:
        for index in range(num_users):
            name = next(names)
            create_user(api, name, organization)
    except ckanapi.errors.NotAuthorized:
        logging.error('ERROR: Not authorized to create users. Check your API key, CKAN configuration '
                      'and auth functions for user_create')


if __name__ == '__main__':
    main()
