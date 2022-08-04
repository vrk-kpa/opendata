import click
import ckan.model as model
import ckanext.ytp_request.model as rmodel


def get_commands():
    return [opendata_request]


@click.group()
def opendata_request():
    'Organization membership request functions'
    pass


@opendata_request.command()
def init_db():
    """
    Connects to the CKAN database and creates the member request tables
    """

    model.Session.remove()
    model.Session.configure(bind=model.meta.engine)

    click.echo("Initializing request tables")
    rmodel.init_tables()
    click.echo("Request tables are setup")
