import os
from celery.task import task
from ckan.logic.action import get
from ckan import model

try:
    from ckanext.archiver import settings
except ImportError:
    from ckanext.archiver import default_settings as settings

@task(name="archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    logger = clean.get_logger()
    logger.error("clean task not implemented yet")


@task(name="archiver.update")
def update(package_id = None, limit = None):
    logger = update.get_logger()

    # load pylons
    from paste.deploy import appconfig
    from ckan.config.environment import load_environment
    conf = appconfig('config:%s' % settings.CKAN_CONFIG)
    load_environment(conf.global_conf, conf.local_conf)

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        logger.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    context = {'model': model, 'session': model.Session,  'user': settings.ARCHIVE_USER}
    data = {}

    if package_id:
        data['id'] = package_id
        package = get.package_show(context, data)
        if package:
            packages = [package]
        else:
            logger.error("Error: Package not found: %s" % package_id)
    else:
        if limit:
            data['limit'] = limit
            logger.info("Limiting results to %d packages" % limit)
        packages = get.current_package_list_with_resources(context, data)

    logger.info("Total packages to update: %d" % len(packages))
    if not packages:
        return

    for package in packages:
        resources = package.get('resources', [])
        if not len(resources):
            logger.info("Package %s has no resources - skipping" % package['name'])
        else:
            logger.info("Checking package: %s (%d resource(s))" % 
                (package['name'], len(resources))
            )
            for resource in resources:
                logger.info("Attempting to archive resource: %s" % resource['url'])
                archive_resource(resource, package['name'])


def archive_resource(resource, package_name, url_timeout=30):
    pass
