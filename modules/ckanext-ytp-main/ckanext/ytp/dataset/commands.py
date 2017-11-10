from ckan.lib.cli import CkanCommand
from ckan.logic import get_action
from ckan import model
import polib
import os
import re
import glob
from ckanext.ytp.dataset.translations import facet_translations


from ckan.plugins.toolkit import config as c

import click

from ckan.lib.cli import (
    load_config,
    parse_db_config,
    paster_click_group,
    click_config_option,
)

import ast

from ckan.lib.munge import munge_title_to_name

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

    context = {'ignore_auth': True,
               'all_fields': True,
               'include_extras': True}


    default_lang = c.get('ckan.locale_default', 'en')


    datasets = get_action('package_list')(context, {})

    package_patches = []
    resource_patches = []


    for dataset in datasets:
        data_dict = {'id': dataset}
        old_package_dict = get_action('package_show')(context, data_dict)

        if old_package_dict.get('title_translated'):
            continue

        original_language = default_lang
        if old_package_dict.get('original_language'):
            original_language = old_package_dict.get('original_language')

        langs = []
        if old_package_dict.get('translations'):
            langs = old_package_dict.get('translations')

        patch = {
            'id': old_package_dict['id'],
            'title_translated': {
                original_language: old_package_dict['title']
            },
            'notes_translated':  {
                original_language: old_package_dict['notes']
            },
            'keywords': { 'fi': [ tag['name'] for tag in old_package_dict['tags'] if tag['vocabulary_id'] is None ] },
            'content_type': {'fi': [ s for s in old_package_dict.get('content_type', "").split(',')]},
            'copyright_notice_translated': {
                original_language: old_package_dict.get('copyright_notice', '')
            },
            'external_urls': old_package_dict.get('extra_information', [])
        }



        for lang in langs:
            patch['title_translated'][lang] = old_package_dict.get('title_' + lang)
            patch['notes_translated'][lang] = old_package_dict.get('notes_' + lang)
            patch['copyright_notice_translated'][lang] = old_package_dict.get('copyright_notice_' + lang)


        if old_package_dict.get('resources'):
            patch['resources'] = old_package_dict.get('resources')

        for resource in patch.get('resources', []):
            resource['name_translated'] = {
                original_language: resource['name']
            }
            resource['description_translated'] = {
                original_language: resource.get('description')
            }
            resource['temporal_granularity'] = {
                original_language: resource.get('temporal_granularity')
            }
            resource['update_frequency'] = {
                original_language: resource.get('update_frequency')
            }

            for lang in langs:
                resource['name_translated'][lang] = resource.get('name_' + lang)
                resource['description_translated'][lang] = resource.get('description_' + lang)
                resource['temporal_granularity'][lang] = resource.get('temporal_granularity_' + lang)
                resource['update_frequency'][lang] = resource.get('update_frequency_' + lang)
            
            #print resource
            #get_action('resource_patch')({}, resource)
        package_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in package_patches)
        print '\n'.join('%s' % p for p in resource_patches)

    else:
        apply_patches(package_patches, resource_patches)

        #get_action('package_patch')({}, old_package_dict)

        #created_dataset = get_action('package_create')({}, new_package_dict)



def apply_patches(package_patches, resource_patches):
    if not package_patches and not resource_patches:
        print 'Nothing to do.'
    else:
        package_patch = get_action('package_patch')
        resource_patch = get_action('resource_patch')
        context = {'ignore_auth': True}
        for patch in package_patches:
            package_patch(context, patch)
        for patch in resource_patches:
            resource_patch(context, patch)


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