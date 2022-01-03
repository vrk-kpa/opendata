import argparse
import datetime
import logging

import ckanapi

'''
Remove USER memmbers from a given organization with a reference parameter
Usage:
    - python remove_organization_members.py -r --reference <id or name of group> [required]
    - python remove_organization_members.py -d --dry-run (optional)
'''


logging.basicConfig(format='%(message)s')


def remove_user_members_from_org(api, reference, dry_run):
    removed_members = []

    member_list = api.action.member_list(id=reference, object_type='user')

    for member in member_list:
        # member = [id, type, capacity]
        if not dry_run:
            api.action.organization_member_delete(id=reference, username=member[0])
        removed_members.append(member)

    return removed_members


def main():
    parser = argparse.ArgumentParser(description='Remove user members from an organization.')
    # For local development, use http://vagrant.avoindata.fi/data as base
    parser.add_argument(
        '-b', '--base',
        default='http://localhost:5000',
        help='Base URL for CKAN API to post to [default: \'%(default)s\'].')

    parser.add_argument(
        '-a', '--apikey',
        default='tester',
        help='API key to post with [default: \'%(default)s\'].')

    parser.add_argument(
        '-r', '--reference',
        required=True,
        help='Reference to the organization, either name or database id. Required.')

    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Prints info about members which will be removed to stdout but does not remove anything from the database.')

    args = parser.parse_args()
    reference = args.reference
    dry_run = args.dry_run

    user_agent_ident = 'remove_org_members-{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.utcnow())

    api = ckanapi.RemoteCKAN(
        args.base,
        apikey=args.apikey,
        user_agent='avoindata_ckanapi_groups/1.0 ({0})'.format(user_agent_ident))

    removed_members = remove_user_members_from_org(api, reference, dry_run)

    print('Organization: %s' % (reference))
    print('Removed members %s' % (removed_members))
    print('Removed members count: %s' % (len(removed_members)))
    print('Dry run: %s' % (dry_run))

    if not dry_run:
        logging.info(removed_members)  # Log list of removed members.


if __name__ == '__main__':
    main()
