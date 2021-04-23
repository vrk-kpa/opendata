# -*- coding: utf8 -*-

from ckan.lib.cli import CkanCommand
from ckan.logic import get_action, ValidationError
from ckan import model
from ckanext.ytp.translations import facet_translations
import ckan.plugins.toolkit as t
import ckan.lib.mailer as mailer
import ckan.lib.plugins as lib_plugins
from datetime import datetime
from pprint import pformat
import polib
import os
import re
import glob
import six
from tools import check_package_deprecation
from logic import send_package_deprecation_emails

from ckan.plugins.toolkit import config as c

import click

from ckan.lib.cli import (
    load_config,
    paster_click_group,
    click_config_option,
)


import itertools


class YtpFacetTranslations(CkanCommand):
    """ Command to add task to schedule table """
    max_args = None
    min_args = 1

    usage = "i18n root path"
    summary = "Add facet translations to database"
    group_name = "ytp-dataset"

    def _add_term(self, context, locale, term, translation):
        get_action('term_translation_update')(context, {'term': term, 'term_translation': translation, 'lang_code': locale})

    def _get_po_files(self, path):
        pattern = re.compile('^[a-z]{2}(?:_[A-Z]{2})?$')

        for locale in os.listdir(path):
            if not pattern.match(locale):
                continue

            for po in glob.glob(os.path.join(path, locale, "LC_MESSAGES/*.po")):
                yield locale, po

    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        return context

    def command(self):
        self._load_config()

        i18n_root = self.args[0]
        terms = facet_translations()
        if len(terms) <= 0:
            print "No terms provided"
            return 1

        translated = []

        for locale, po_path in self._get_po_files(i18n_root):
            found = 0
            for entry in polib.pofile(po_path):
                if entry.msgid in terms:
                    translated.append((locale, entry.msgid, entry.msgstr))
                    found += 1
            if found != len(terms):
                print "Term not found"
                return 1

        for term in terms:
            translated.append(('en', term, term))

        context = self._create_context()

        for locale, term, translation in translated:
            if translation:
                self._add_term(context, locale, term, translation)


ytp_dataset_group = paster_click_group(
    summary=u'Dataset related commands.'
)


@ytp_dataset_group.command(
    u'migrate_author_email',
    help=u'Migrates empty author emails that caused problems in updating datasets'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_author_email(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])
    package_patches = []

    for old_package_dict in package_generator('*:*', 10):
        if old_package_dict.get('author_email') is None:
            patch = {'id': old_package_dict['id'], 'author_email': ''}
            package_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in package_patches)
    else:
        # No resources patches so empty parameter is passed
        apply_patches(package_patches, [])


@ytp_dataset_group.command(
    u'migrate',
    help=u'Migrates datasets to scheming based model'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    default_lang = c.get('ckan.locale_default', 'en')

    package_patches = []
    resource_patches = []

    for old_package_dict in package_generator('*:*', 10):

        if 'title_translated' in old_package_dict:
            continue

        original_language = old_package_dict.get('original_language', default_lang)

        langs = old_package_dict.get('translations', [])

        patch = {
            'id': old_package_dict['id'],
            'title_translated': {
                original_language: old_package_dict['title']
            },
            'notes_translated':  {
                original_language: old_package_dict['notes']
            },
            'copyright_notice_translated': {
                original_language: old_package_dict.get('copyright_notice', '')
            },
            'external_urls': old_package_dict.get('extra_information', [])
        }

        if old_package_dict.get('tags'):
            patch['keywords'] = {'fi': [tag['name']
                                        for tag in old_package_dict.get('tags', []) if tag['vocabulary_id'] is None]}

        if old_package_dict.get('content_type'):
            patch['content_type'] = {'fi': [s for s in old_package_dict.get('content_type', "").split(',') if s]}

        if old_package_dict.get('license_id') is None:
            patch['license_id'] = 'other'

        for lang in langs:
            patch['title_translated'][lang] = old_package_dict.get('title_' + lang, '')
            patch['notes_translated'][lang] = old_package_dict.get('notes_' + lang, '')
            patch['copyright_notice_translated'][lang] = old_package_dict.get('copyright_notice_' + lang, '')

        patch['resources'] = old_package_dict.get('resources')

        for resource in patch.get('resources', []):
            resource['name_translated'] = {
                original_language: resource.get('name', '') or ''
            }
            resource['description_translated'] = {
                original_language: resource.get('description', '') or ''
            }
            if resource.get('temporal_granularity') and type(resource.get('temporal_granularity')) is not dict:
                resource['temporal_granularity'] = {
                    original_language: resource.get('temporal_granularity')
                }
            else:
                del resource['temporal_granularity']
            if resource.get('update_frequency') and type(resource.get('update_frequency')) is not dict:
                resource['update_frequency'] = {
                    original_language: resource.get('update_frequency')
                }
            else:
                del resource['update_frequency']

            for lang in langs:
                resource['name_translated'][lang] = resource.get('name_' + lang, '')
                resource['description_translated'][lang] = resource.get('description_' + lang, '')
                if resource.get('temporal_granularity_' + lang):
                    resource['temporal_granularity'][lang] = resource.get('temporal_granularity_' + lang)
                if resource.get('temporal_granularity_' + lang):
                    resource['update_frequency'][lang] = resource.get('update_frequency_' + lang)

        package_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in package_patches)
        print '\n'.join('%s' % p for p in resource_patches)
    else:
        apply_patches(package_patches, resource_patches)


@ytp_dataset_group.command(
    u'migrate_temporal_granularity',
    help=u'Migrates old schema temporal granularity (string) to the new time_series_precision format (["string"])'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_temporal_granularity(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    package_patches = []

    for old_package_dict in package_generator('*:*', 10):
        resource_patches = []
        changes = False
        for resource in old_package_dict.get('resources', []):
            temporal_granularity = resource.get('temporal_granularity')
            if temporal_granularity and len(temporal_granularity) > 0:
                for k, v in temporal_granularity.items():
                    if isinstance(v, basestring) and len(v) > 0:
                        temporal_granularity[k] = [v]
                        changes = True
                    elif isinstance(v, basestring):
                        temporal_granularity.pop(k)
                        changes = True
            resource_patches.append(resource)
        if changes:
            # Resources need to patched all at once, so they are moved to package patch
            patch = {'id': old_package_dict['id'], 'resources': resource_patches}
            package_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in package_patches)
    else:
        # No resource patches so empty parameter is passed
        apply_patches(package_patches, [])


@ytp_dataset_group.command(
    u'migrate_high_value_datasets',
    help=u'Migrates high value datasets to international benchmarks'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_high_value_datasets(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])
    package_patches = []

    for old_package_dict in package_generator('*:*', 10):
        if old_package_dict.get('high_value_dataset_category'):
            patch = {'id': old_package_dict['id'], 'international_benchmarks': old_package_dict['high_value_dataset_category']}
            package_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in package_patches)
    else:
        # No resources patches so empty parameter is passed
        apply_patches(package_patches, [])


def apply_patches(package_patches, resource_patches):
    if not package_patches and not resource_patches:
        print 'No patches to process.'
    else:
        package_patch = get_action('package_patch')
        resource_patch = get_action('resource_patch')
        context = {'ignore_auth': True}
        for patch in package_patches:
            try:
                package_patch(context, patch)
            except ValidationError as e:
                print "Migration failed for package %s reason:" % patch['id']
                print e
        for patch in resource_patches:
            try:
                resource_patch(context, patch)
            except ValidationError as e:
                print "Migration failed for resource %s, reason" % patch['id']
                print e


def apply_group_assigns(group_packages_map):
    if not group_packages_map:
        print 'No group memberships to set.'
    else:
        member_create = get_action('member_create')
        context = {'ignore_auth': True}

        for group, packages in group_packages_map.items():
            for package in packages:
                data = {'id': group,
                        'object': package,
                        'object_type': 'package',
                        'capacity': 'public'}
                try:
                    member_create(context, data)
                except Exception as e:
                    print "Group assign failed for package %s reason:" % package
                    print e


def package_generator(query, page_size, context={'ignore_auth': True}, dataset_type='dataset'):
    package_search = get_action('package_search')

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict = {'include_private': True, 'rows': page_size, 'q': query, 'start': index,
                     'fq': '+dataset_type:' + dataset_type}
        data = package_search(context, data_dict)
        packages = data.get('results', [])
        for package in packages:
            yield package

        # Stop iteration all query results have been looped through
        if data["count"] < (index + page_size):
            return


@ytp_dataset_group.command(
    u'batch_edit',
    help=u'Make modifications to many datasets at once'
)
@click_config_option
@click.argument('search_string')
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--group', help="Make datasets members of a group")
@click.pass_context
def batch_edit(ctx, config, search_string, dryrun, group):
    load_config(config or ctx.obj['config'])
    group_assigns = {}

    if group:
        group_assigns[group] = []

    for package_dict in package_generator(search_string, 10):
        if group:
            group_assigns[group].append(package_dict['name'])

    if dryrun:
        print '\n'.join('Add %s to group %s' % (p, g) for (g, ps) in group_assigns.items() for p in ps)
    else:
        if group:
            apply_group_assigns(group_assigns)


@ytp_dataset_group.command(
    u'update_package_deprecation',
    help=u'Checks package deprecation and updates it if it need updating, and sends emails to users'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def update_package_deprecation(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])
    # deprecation emails will be sent to items inside deprecated_now array
    deprecated_now = []
    package_patches = []

    # Get only packages with a valid_till field and some value in the valid_till field
    for old_package_dict in package_generator('valid_till:* AND -valid_till:""', 10):
        valid_till = old_package_dict.get('valid_till')

        # For packages that have a valid_till date set depracated field to true or false
        # deprecation means that a package has been valid but is now old and not valid anymore.
        # This does not take into account if the package is currently valid eg. valid_from.
        if valid_till is not None:
            current_deprecation = old_package_dict.get('deprecated')
            deprecation = check_package_deprecation(valid_till)
            if current_deprecation != deprecation:
                patch = {'id': old_package_dict['id'], 'deprecated': deprecation}
                package_patches.append(patch)
                # Send email only when actually deprecated. Initial deprecation is undefined when adding this feature
                if current_deprecation is False and deprecation is True:
                    deprecated_now.append(old_package_dict['id'])

    if dryrun:
        print '\n'.join(('%s | %s' % (p, p['id'] in deprecated_now)) for p in package_patches)
    else:
        # No resources patches so empty parameter is passed
        apply_patches(package_patches, [])
        send_package_deprecation_emails(deprecated_now)


@ytp_dataset_group.command(
    u'validate',
    help=u'Validate datasets'
)
@click_config_option
@click.option(u'--verbose', is_flag=True)
@click.pass_context
def validate(ctx, config, verbose):
    load_config(config or ctx.obj['config'])

    no_errors = True
    user = t.get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})
    context = {'model': model, 'session': model.Session, 'user': user['name'], 'ignore_auth': True}
    for package_dict in package_generator('*:*', 10):
        if verbose:
            print "Validating %s" % package_dict['name']

        if 'type' not in package_dict:
            package_plugin = lib_plugins.lookup_package_plugin()
            try:
                # use first type as default if user didn't provide type
                package_type = package_plugin.package_types()[0]
            except (AttributeError, IndexError):
                package_type = 'dataset'
                # in case a 'dataset' plugin was registered w/o fallback
                package_plugin = lib_plugins.lookup_package_plugin(package_type)
            package_dict['type'] = package_type
        else:
            package_plugin = lib_plugins.lookup_package_plugin(package_dict['type'])

        schema = package_plugin.update_package_schema()

        data, errors = lib_plugins.plugin_validate(
            package_plugin, context, package_dict, schema, 'package_update')

        if errors:
            no_errors = False
            print package_dict['name']
            print pformat(errors)
            print

    if no_errors:
        print 'All datasets are valid!'


ytp_org_group = paster_click_group(
    summary=u'Organization related commands.'
)


@ytp_org_group.command(
    u'migrate',
    help=u'Migrates organizations to scheming based model'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_orgs(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    default_lang = c.get('ckan.locale_default', 'en')
    languages = ['fi', 'en', 'sv']
    translated_fields = ['title', 'description']

    org_patches = []

    for old_org_dict in org_generator():
        flatten_extras(old_org_dict)

        patch = {}

        for field in translated_fields:
            translated_field = '%s_translated' % field
            if translated_field not in old_org_dict:
                patch[translated_field] = {default_lang: old_org_dict[field]}
                for language in languages:
                    value = old_org_dict.get('%s_%s' % (field, language))
                    if value is not None and value != "":
                        patch[translated_field][language] = value
            else:
                patch[field] = old_org_dict[translated_field].get(default_lang)

        if 'features' not in old_org_dict:
            # 'adminstration' is used in previous data model
            if old_org_dict.get('public_adminstration_organization'):
                patch['features'] = ["public_administration_organization"]

        if patch:
            patch['id'] = old_org_dict['id']
            org_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in org_patches)
    else:
        apply_org_patches(org_patches)


def apply_org_patches(org_patches):
    if not org_patches:
        print 'No patches to process.'
    else:
        org_patch = get_action('organization_patch')
        context = {'ignore_auth': True}
        for patch in org_patches:
            try:
                org_patch(context, patch)
            except ValidationError as e:
                print "Migration failed for organization %s reason:" % patch['id']
                print e


def org_generator():
    context = {'ignore_auth': True}
    org_list = get_action('organization_list')
    orgs = org_list(context, {'all_fields': True, 'include_extras': True})
    for org in orgs:
        yield org


def flatten_extras(o):
    active_extras = (e for e in o.get('extras', []) if e['state'] == 'active')
    for e in active_extras:
        key = e['key']
        value = e['value']
        while key in o:
            key = '%s_extra' % key
        o[key] = value


opendata_group = paster_click_group(
    summary=u'Group related commands.'
)


@opendata_group.command(
    u'add',
    help="Adds all users to all groups as editors"
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def add_to_groups(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    context = {'ignore_auth': True}
    groups = get_action('group_list')(context, {})
    users = get_action('user_list')(context, {})

    data_dicts = []
    for group in groups:
        memberships = get_action('member_list')(context, {'id': group})
        for user in users:
            if not any(id for (id, type, capacity) in memberships if id == user['id']):
                data_dicts.append({'id': group, 'username': user['name'], 'role': 'editor'})

    if dryrun:
        print '\n'.join('%s' % d for d in data_dicts)
    else:
        for d in data_dicts:
            get_action('group_member_create')(context, d)


opendata_harvest_group = paster_click_group(
    summary=u'Harvester related commands.'
)


@opendata_harvest_group.command(
    u'send-status-emails',
    help='Sends harvester status emails to configured recipients'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--force', is_flag=True)
@click.option(u'--all-harvesters', is_flag=True)
@click.pass_context
def send_harvester_status_emails(ctx, config, dryrun, force, all_harvesters):
    load_config(config or ctx.obj['config'])

    email_notification_recipients = t.aslist(t.config.get('ckanext.ytp.harvester_status_recipients', ''))

    if not email_notification_recipients and not dryrun:
        print 'No recipients configured'
        return

    status_opts = {} if not all_harvesters else {'include_manual': True, 'include_never_run': True}
    status = get_action('harvester_status')({}, status_opts)

    errored_runs = any(item.get('errors') != 0 for item in status.values())
    running = (item.get('started') for item in status.values() if item.get('status') == 'running')
    stuck_runs = any(_elapsed_since(started).days > 1 for started in running)

    if not (errored_runs or stuck_runs) and not force:
        print 'Nothing to report'
        return

    if len(status) == 0:
        print 'No harvesters matching criteria found'
        return

    site_title = t.config.get('ckan.site_title', '')
    today = datetime.now().date().isoformat()

    status_templates = {
            'running': '%%(title)-%ds | Running since %%(time)s with %%(errors)d errors',
            'finished': '%%(title)-%ds | Finished %%(time)s with %%(errors)d errors',
            'pending': '%%(title)-%ds | Pending since %%(time)s'}
    unknown_status_template = '%%(title)-%ds | Unknown status: %%(status)s'
    max_title_length = max(len(title) for title in status)

    def status_string(title, values):
        template = status_templates.get(values.get('status'), unknown_status_template)
        status = values.get('status')
        time_field = 'finished' if status == 'finished' else 'started'
        return template % max_title_length % {
                'title': title,
                'time': _pretty_time(values.get(time_field)),
                'status': status,
                'errors': values.get('errors')
                }

    msg = '%(site_title)s - Harvester summary %(today)s\n\n%(status)s' % {
            'site_title': site_title,
            'today': today,
            'status': '\n'.join(status_string(title, values) for title, values in status.items())
            }

    subject = '%s - Harvester summary %s' % (site_title, today)
    _send_harvester_notification(subject, msg, email_notification_recipients, dryrun)

    if dryrun:
        print msg


@opendata_harvest_group.command(
    u'send-stuck-runs-report',
    help='Sends stuck runs report to configured recipients'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--force', is_flag=True)
@click.option(u'--all-harvesters', is_flag=True)
@click.pass_context
def send_stuck_runs_report(ctx, config, dryrun, force, all_harvesters):
    load_config(config or ctx.obj['config'])

    email_notification_recipients = t.aslist(t.config.get('ckanext.ytp.fault_recipients', ''))

    if not email_notification_recipients and not dryrun:
        print('No recipients configured')
        return

    status_opts = {} if not all_harvesters else {'include_manual': True, 'include_never_run': True}
    status = get_action('harvester_status')({}, status_opts)

    stuck_runs = [(title, job_status) for title, job_status in six.iteritems(status)
                  if job_status.get('status') == 'running' and _elapsed_since(job_status.get('started')).days > 1]

    if stuck_runs:
        site_title = t.config.get('ckan.site_title', '')

        msg = '%(site_title)s - Following harvesters have been running more than 24 hours: \n\n%(status)s\n\n' \
              'Instructions to fix this can be found from here %(instructions)s' % \
              {
                  'site_title': site_title,
                  'status': '\n'.join('%s has been stuck since %s' %
                                      (title, status.get('started')) for title, status in stuck_runs),
                  'instructions': t.config.get('ckanext.ytp.harvester_instruction_url', 'url not configured')
              }

        subject = '%s - There are stuck harvester runs that need to have a look at' % site_title
        _send_harvester_notification(subject, msg, email_notification_recipients, dryrun)

        if dryrun:
            print(msg)
    else:
        print('Nothing to report')


def _send_harvester_notification(subject, msg, recipients, dryrun):

    for recipient in recipients:
        email = {'recipient_name': recipient,
                 'recipient_email': recipient,
                 'subject': subject,
                 'body': msg}

        if dryrun:
            print('to: %s' % recipient)
        else:
            try:
                mailer.mail_recipient(**email)
            except mailer.MailerException as e:
                print('Sending harvester notification to %s failed: %s' % (recipient, e))


def _elapsed_since(t):
    if t is None:
        return t
    if isinstance(t, str):
        t = datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
    return datetime.now() - t


def _pretty_time(t):
    if t is None:
        return 'unknown'

    delta = _elapsed_since(t)
    if delta.days == 0:
        return 'today'
    if delta.days == 1:
        return 'yesterday'
    elif delta.days < 30:
        return '%d days ago' % delta.days
    elif delta.days < 365:
        return '%d months ago' % int(delta.days / 30)
    else:
        return '%d years ago' % int(delta.days / 365)
