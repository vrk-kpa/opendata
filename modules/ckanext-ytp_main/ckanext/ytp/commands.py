from ckan.lib.cli import CkanCommand
from ckan.logic import get_action
from ckan import model
import polib
import os
import re
import glob
from ckanext.ytp.translations import facet_translations
from ckan.logic import ValidationError

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

    for old_package_dict in package_generator('*:*', 1000):

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
            patch['keywords'] = {'fi': [tag['name'] for tag in old_package_dict.get('tags', []) if tag['vocabulary_id'] is None]}

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


def package_generator(query, page_size):
    context = {'ignore_auth': True}
    package_search = get_action('package_search')

    for index in itertools.count(start=0, step=page_size):
        data_dict = {'include_private': True, 'rows': page_size, 'q': query, 'start': index}
        packages = package_search(context, data_dict).get('results', [])
        for package in packages:
            yield package
        else:
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

    for package_dict in package_generator(search_string, 1000):
        if group:
            group_assigns[group].append(package_dict['name'])

    if dryrun:
        print '\n'.join('Add %s to group %s' % (p, g) for (g, ps) in group_assigns.items() for p in ps)
    else:
        if group:
            apply_group_assigns(group_assigns)


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
