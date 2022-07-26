from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import types

from ckan.plugins import toolkit as tk
from ckan.model.meta import metadata, mapper, Session
from ckan import model
from ckanext.showcase.model import ShowcaseBaseModel

import logging
log = logging.getLogger(__name__)

showcase_apiset_assocation_table = None


def setup():
    if showcase_apiset_assocation_table is None:
        define_showcase_apiset_association_table()
        log.debug('ShowcaseApisetAssociation table defined in memory')

    if model.package_table.exists() and 'apis' in tk.config.get('ckan.plugins'):
        if not showcase_apiset_assocation_table.exists():
            showcase_apiset_assocation_table.create()
            log.debug('ShowcaseApisetAssociation table create')
        else:
            log.debug('ShowcaseApisetAssociation table already exists')
    else:
        log.debug('ShowcaseApisetAssociation table creation deferred')


class ShowcaseApisetAssociation(ShowcaseBaseModel):

    @classmethod
    def get_apiset_ids_for_showcase(cls, showcase_id):
        '''
        Return a list of apiset ids associated with the passed showcase_id.
        '''
        showcase_apiset_association_list = \
            Session.query(cls.package_id).filter_by(
                showcase_id=showcase_id).all()
        return showcase_apiset_association_list

    @classmethod
    def get_showcase_ids_for_apiset(cls, package_id):
        '''
        Return a list of showcase ids associated with the passed package_id.
        '''
        showcase_apiset_association_list = \
            Session.query(cls.showcase_id).filter_by(
                package_id=package_id).all()
        return showcase_apiset_association_list


def define_showcase_apiset_association_table():
    global showcase_apiset_assocation_table

    showcase_apiset_assocation_table = Table(
        'showcase_apiset_association', metadata,
        Column('package_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False),
        Column('showcase_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False)
    )

    mapper(ShowcaseApisetAssociation, showcase_apiset_assocation_table)
