# -*- coding: utf8 -*-

from ckan.logic import get_action, ValidationError, NotFound
import ckan.plugins.toolkit as toolkit

import itertools

import click


def get_commands():
    return [sixodp_showcase]


@click.group()
def sixodp_showcase():
    'Showcase related commands.'
    pass


@sixodp_showcase.command(
    u'migrate_title_to_title_translated',
    help=u'Migrates old schema title to the new multi-lang title'
)
@click.option(u'--dryrun', is_flag=True)
def migrate_title_to_title_translated(dryrun):
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
        click.echo('\n'.join('%s' % p for p in showcase_patches))
    else:
        # No resource patches so empty parameter is passed
        apply_patches(showcase_patches, [])


@sixodp_showcase.command(
    u'create_platform_vocabulary',
    help=u'Creates a platforms vocabulary to use as a preset list of options'
)
@click.option(u'--dryrun', is_flag=True)
def create_platform_vocabulary(dryrun):
    context = {'ignore_auth': True}
    vocab_id = 'platform'
    tags = (u"Android", u"iOS Apple", u"Windows", u"Mac OS X", u"Website", u"Other")
    tags_to_delete = []
    tags_to_create = []
    if dryrun:
        click.echo("-- Dryrun --")
    try:
        data = {'id': vocab_id}
        old_tags = toolkit.get_action('vocabulary_show')(context, data)
        click.echo('Platform vocabulary found; clearing old tags if needed')
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
        click.echo('Platform vocabulary not found')
        data = {'name': vocab_id}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        click.echo('Platform vocabulary created')
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tags_to_create.append({'name': tag})
            if dryrun:
                continue
            else:
                toolkit.get_action('tag_create')(context, data)

    if len(tags_to_create) > 0 or len(tags_to_delete) > 0:
        click.echo("Tags to be deleted:" if dryrun else "Deleted tags:")
        click.echo(tags_to_delete)
        click.echo("")
        click.echo("Tags to be created:" if dryrun else "Created tags:")
        click.echo(tags_to_create)
        click.echo("")
    else:
        click.echo("No changes")


@sixodp_showcase.command(
    u'migrate_website_showcase_type_to_platform',
    help=u'Migrates old website info from showcase_type to platform'
)
@click.pass_context
@click.option(u'--dryrun', is_flag=True)
def migrate_website_showcase_type_to_platform(ctx, dryrun):
    showcase_patches = []
    for old_showcase_dict in package_generator('*:*', 1000, dataset_type='showcase'):
        if 'showcase_type' not in old_showcase_dict:
            continue

        showcase_platforms = old_showcase_dict.get('platform', [])
        if 'Website' in old_showcase_dict.get('showcase_type', []) and 'Website' not in showcase_platforms:
            showcase_platforms.append('Website')
            showcase_patches.append({
                'id': old_showcase_dict['id'],
                'platform': showcase_platforms,
            })

    if dryrun:
        click.echo('\n'.join('%s' % p for p in showcase_patches))
    else:
        flask_app = ctx.meta['flask_app']
        # Current user is tested agains sysadmin role during model
        # dictization, thus we need request context
        with flask_app.test_request_context():
            # No resource patches so empty parameter is passed
            apply_patches(showcase_patches, [])


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
        click.echo('No patches to process.')
    else:
        package_patch = get_action('package_patch')
        resource_patch = get_action('resource_patch')
        site_user = get_action(u'get_site_user')({
            u'ignore_auth': True},
            {}
        )
        toolkit.g.user = site_user['name']
        context = {
            u'ignore_auth': True,
            u'user': site_user['name'],
        }
        for patch in package_patches:
            try:
                package_patch(context, patch)
            except ValidationError as e:
                click.echo("Migration failed for package %s reason:" % patch['id'])
                click.echo(e)
        for patch in resource_patches:
            try:
                resource_patch(context, patch)
            except ValidationError as e:
                click.echo("Migration failed for resource %s, reason" % patch['id'])
                click.echo(e)
