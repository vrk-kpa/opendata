# -*- coding: utf8 -*-

from ckan.logic import get_action, ValidationError, NotFound
import ckan.plugins.toolkit as toolkit

import itertools

import click

from ckan.lib.cli import (
    load_config,
    paster_click_group,
    click_config_option,
)


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


sixodp_showcase_group = paster_click_group(
    summary=u'Showcase related commands.'
)


@sixodp_showcase_group.command(
    u'migrate_title_to_title_translated',
    help=u'Migrates old schema title to the new multi-lang title'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_title_to_title_translated(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    showcase_patches = []

    for old_showcase_dict in package_generator('*:*', 1000, dataset_type='showcase'):

        if 'title_translated' in old_showcase_dict:
            continue

        title = old_showcase_dict.get('title')

        patch = {
            'id': old_showcase_dict['id'],
            'title_translated': {
                'fi': title
            }
        }

        showcase_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in showcase_patches)
    else:
        # No resource patches so empty parameter is passed
        apply_patches(showcase_patches, [])


@sixodp_showcase_group.command(
    u'create_platform_vocabulary',
    help=u'Creates a platforms vocabulary to use as a preset list of options'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def create_platform_vocabulary(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])
    context = {'ignore_auth': True}
    vocab_id = 'platform'
    tags = (u"Android", u"iOS Apple", u"Windows", u"Mac OS X", u"Other")
    tags_to_delete = []
    tags_to_create = []
    if dryrun:
        print "-- Dryrun --"
    try:
        data = {'id': vocab_id}
        old_tags = toolkit.get_action('vocabulary_show')(context, data)
        print 'Platform vocabulary found; clearing old tags if needed'
        for old_tag in old_tags.get('tags'):

            if old_tag['id'] in tags:
                continue
            else:
                tags_to_delete.append({'name': old_tag['name']})
                if dryrun:
                    continue
                else:
                    toolkit.get_action('tag_delete')(context, {'id': old_tag['id']})
        for tag in tags:
            try:
                toolkit.get_action('tag_show')(context, {'id': tag, 'vocabulary_id': vocab_id})
            except toolkit.ObjectNotFound:
                tags_to_create.append({'name': tag})
                if dryrun:
                    continue
                else:
                    toolkit.get_action('tag_create')(context, {'name': tag, 'vocabulary_id': old_tags.get('id')})
    except NotFound:
        print 'Platform vocabulary not found'
        data = {'name': vocab_id}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        print 'Platform vocabulary created'
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tags_to_create.append({'name': tag})
            if dryrun:
                continue
            else:
                toolkit.get_action('tag_create')(context, data)

    if len(tags_to_create) > 0 or len(tags_to_delete) > 0:
        print "Tags to be deleted:" if dryrun else "Deleted tags:"
        print tags_to_delete
        print ""
        print "Tags to be created:" if dryrun else "Created tags:"
        print tags_to_create
        print ""
    else:
        print "No changes"


@sixodp_showcase_group.command(
    u'create_showcase_type_vocabulary',
    help=u'Creates a showcase_type vocabulary to use as a preset list of options'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def create_showcase_type_vocabulary(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])
    context = {'ignore_auth': True}
    vocab_id = 'showcase_type'
    tags = (u"Mobile application", u"Other application", u"Tools", u"Website", u"Visualisation")
    tags_to_delete = []
    tags_to_create = []
    if dryrun:
        print "-- Dryrun --"
    try:
        data = {'id': vocab_id}
        old_tags = toolkit.get_action('vocabulary_show')(context, data)
        print 'Showcase type vocabulary found; clearing old tags if needed'
        for old_tag in old_tags.get('tags'):
            if old_tag['name'] in tags:
                continue
            else:
                tags_to_delete.append({'name': old_tag['name']})
                if dryrun:
                    continue
                toolkit.get_action('tag_delete')(context, {'id': old_tag['id']})
        for tag in tags:
            try:
                toolkit.get_action('tag_show')(context, {'id': tag, 'vocabulary_id': vocab_id})
            except toolkit.ObjectNotFound:
                tags_to_create.append({'name': tag})
                if dryrun:
                    continue
                toolkit.get_action('tag_create')(context, {'name': tag, 'vocabulary_id': old_tags.get('id')})
    except NotFound:
        print 'Showcase type vocabulary not found'
        data = {'name': vocab_id}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        print 'Showcase type vocabulary created'
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tags_to_create.append({'name': tag})
            if dryrun:
                continue
            else:
                toolkit.get_action('tag_create')(context, data)

    if len(tags_to_create) > 0 or len(tags_to_delete) > 0:
        print "Tags to be deleted:" if dryrun else "Deleted tags:"
        print tags_to_delete
        print ""
        print "Tags to be created:" if dryrun else "Created tags:"
        print tags_to_create
        print ""
    else:
        print "No changes"


@sixodp_showcase_group.command(
    u'migrate_category_to_showcase_type_and_new_categories',
    help=u'Migrates old showcase category to the new showcase_type AND new showcase (dataset) categories'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.pass_context
def migrate_category_to_showcase_type_and_new_categories(ctx, config, dryrun):
    load_config(config or ctx.obj['config'])

    context = {'ignore_auth': True}
    showcase_patches = []
    showcase_type_options = toolkit.get_action('vocabulary_show')(context, {'id': 'showcase_type'}).get('tags', [])
    showcase_type_options = list(map(lambda x: x['name'], showcase_type_options))

    for old_showcase_dict in package_generator('*:*', 1000, dataset_type='showcase'):

        if 'showcase_type' in old_showcase_dict:
            continue

        new_showcase_categories = []
        new_showcase_types = []
        new_showcase_keywords = old_showcase_dict.get('keywords', {})

        old_showcase_categories = old_showcase_dict.get('category', {})

        if old_showcase_categories:
            old_showcase_categories = old_showcase_categories

        for showcase_category in old_showcase_categories.get('en', []):
            if showcase_category in showcase_type_options:
                new_showcase_types.append(showcase_category)
            else:
                if showcase_category == 'Maps':
                    new_showcase_categories.append("alueet-ja-kaupungit")
                elif showcase_category == 'Transport':
                    new_showcase_categories.append("liikenne")
                elif showcase_category == 'Economy':
                    new_showcase_categories.append("talous-ja-rahoitus")
                elif showcase_category == 'Environment and nature':
                    new_showcase_categories.append("ymparisto-ja-luonto")
                elif showcase_category == 'Government':
                    new_showcase_categories.append("hallinto-ja-julkinen-sektori")
                elif showcase_category == 'Population':
                    new_showcase_categories.append("vaesto-ja-yhteiskunta")
                elif showcase_category == 'Health':
                    new_showcase_categories.append("terveys")
                elif showcase_category == 'Maps':
                    new_showcase_keywords.setdefault('fi', ['Kartat']).append('Kartat')
                    new_showcase_keywords.setdefault('en', ['Maps']).append('Maps')
                    new_showcase_keywords.setdefault('sv', ['Kartor']).append('Kartor')
                elif showcase_category == 'Enterprise':
                    new_showcase_keywords.setdefault('fi', ['Yritys']).append('Yritys')
                    new_showcase_keywords.setdefault('en', ['Enterprise']).append('Enterprise')
                    new_showcase_keywords.setdefault('sv', ['Företag']).append('Företag')

        showcase_categories_fi = old_showcase_categories.get('fi', [])
        if 'Ilmoitetut' in showcase_categories_fi:
            new_showcase_keywords.setdefault('fi', ['Ilmoitetut']).append('Ilmoitetut')

        patch = {
            'id': old_showcase_dict['id'],
            'showcase_type': new_showcase_types,
            'category': new_showcase_categories,
            'keywords': new_showcase_keywords
        }

        showcase_patches.append(patch)

    if dryrun:
        print '\n'.join('%s' % p for p in showcase_patches)
    else:
        # No resource patches so empty parameter is passed
        apply_patches(showcase_patches, [])
