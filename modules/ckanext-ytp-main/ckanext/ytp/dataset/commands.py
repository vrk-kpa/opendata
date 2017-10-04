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
@click.pass_context
def migrate(ctx, config):
    load_config(config or ctx.obj['config'])

    context = {'ignore_auth': True,
               'all_fields': True,
               'include_extras': True}


    default_lang = c.get('ckan.locale_default', 'en')


    datasets = get_action('package_list')(context, {})




    for dataset in datasets:
        data_dict = {'id': dataset}
        old_package_dict = get_action('package_show')(context, data_dict)

        extras = {x['key']: x['value'] for x in old_package_dict.get('extras', {})}

        original_language = default_lang
        if extras.get('original_language'):
            original_language = extras.get('original_language')

        langs = []
        if extras.get('translations'):
            langs = ast.literal_eval(extras.get('translations'))

        new_package_dict = {
            'id': old_package_dict['id'],
            'title_translated': {
                original_language: old_package_dict['title']
            },
            'notes_translated':{
                original_language: old_package_dict['notes']
            },
            'collection_type': extras.get('collection_type', 'Open Data')
        }

        for lang in langs:
            new_package_dict['title_translated'][u'' + lang] = extras.get('title_' + lang)
            new_package_dict['notes_translated'][u''+ lang] = extras.get('notes_' + lang)
        print(new_package_dict)

    print(datasets)