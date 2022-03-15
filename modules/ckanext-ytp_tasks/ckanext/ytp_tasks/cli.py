import click
from ckan.logic import get_action
import ckan.model as model


def get_commands():
    return [opendata_tasks]


@click.group()
def opendata_tasks():
    """Opendata tasks functions
    """
    pass


@opendata_tasks.command()
@click.argument(u"id")
@click.argument(u"name")
@click.argument(u"frequency")
@click.argument(u"data")
@click.option(
    "-w",
    "--wait",
    default=None,
    help="""Execute task now and wait for task in seconds"""
)
@click.option(
    "-e",
    "--execute",
    default=False,
    is_flag=True,
    help="""Execute task now"""
)
def add(id, name, frequency, data, wait, execute):
    """Command to add task to schedule table
    """
    click.echo("Add task into a database")
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    get_action('ytp_tasks_add')(context, {'id': id,
                                          'task': name,
                                          'frequency': frequency.upper(),
                                          'data': data})
    click.echo("Task added")

    if wait or execute:
        import ckan.lib.jobs as jobs

        click.echo("Execute task")
        if wait:
            jobs.enqueue(name, [data], rq_kwargs={"timeout": int(wait)})
        else:
            jobs.enqueue(name, [data])
        click.echo("Task executed")


@opendata_tasks.command()
def execute_all():
    """Command to execute all scheduled tasks
    """
    import ckan.lib.jobs as jobs
    click.echo("Execute all scheduled tasks")
    jobs.enqueue("ckanext.ytp_tasks.tasks.execute_all")
    click.echo("Execute all set to queue")


@opendata_tasks.command()
def init_db():
    """Initializes database tables for ytp-tasks-module
    """
    from ckanext.ytp_tasks.model import YtpTaskTables
    click.echo("Initialize tasks tables")
    YtpTaskTables.create_tables()
    click.echo("Task tables ready")
