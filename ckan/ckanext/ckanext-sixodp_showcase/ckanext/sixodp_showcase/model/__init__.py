from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import types

from ckan.plugins import toolkit as tk
from ckan.model.meta import metadata, mapper, Session
from ckan import model
from ckanext.showcase.model import ShowcaseBaseModel, BaseModel

import logging
log = logging.getLogger(__name__)


class ShowcaseApisetAssociation(ShowcaseBaseModel, BaseModel):

    __tablename__ = "showcase_apiset_association"

    package_id = Column(
        types.UnicodeText,
        ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    showcase_id = Column(
        types.UnicodeText,
        ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
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
