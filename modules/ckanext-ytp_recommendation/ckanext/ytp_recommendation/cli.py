import click
from ckanext.ytp_recommendation.model import init_tables
import ckan.model as model


def get_commands():
    return [recommendations]


@click.group()
def recommendations():
    pass


@recommendations.command()
def init():
    init_tables(model.meta.engine)
