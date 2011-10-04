from celery.task import task

@task(name="archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    logger = clean.get_logger()
    logger.error("clean task not implemented yet")


@task(name="archiver.update")
def update(package_id = None):
    logger = update.get_logger()
    logger.error("update task not implemented yet")
