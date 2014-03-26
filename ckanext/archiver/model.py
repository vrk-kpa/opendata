import json
import uuid
from datetime import datetime

from sqlalchemy import Column, MetaData
from sqlalchemy import types
from sqlalchemy.orm import mapper
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model
from ckan.lib.base import *

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uuid4())

metadata = MetaData()

class ArchiveTask(Base):
    """
    Contains the latest information for archive tasks where each
    entry (by resource_id/dataset_id) is the most recent result.
    """
    __tablename__ = 'archive_task'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    dataset_id = Column(types.UnicodeText, nullable=False, index=True)
    resource_id = Column(types.UnicodeText, nullable=False, index=True)

    response = Column(types.UnicodeText)
    error = Column(types.UnicodeText)
    first_failure = Column(types.DateTime)
    last_success = Column(types.DateTime)
    url_redirected_to = Column(types.UnicodeText)

    reason = Column(types.UnicodeText)
    status = Column(types.UnicodeText)
    failure_count = Column(types.Integer, default=0)

    created   = Column(types.DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_for_resource(cls, resource_id):
        return model.Session.query(cls).filter(cls.resource_id==resource_id).first()

    @classmethod
    def create(cls, entity):
        c = cls()

        c.resource_id = entity.get('entity_id')
        c.response = entity.get('value')
        c.created = entity.get('last_updated')

        # We need to find the dataset_id for the resource.
        q = """
            SELECT P.id from package P
            INNER JOIN resource_group RG ON RG.package_id = P.id
            INNER JOIN resource R ON R.resource_group_id = RG.id
            WHERE R.id = '%s';
        """
        row = model.Session.execute(q % c.resource_id).first()
        if not row or not row[0]:
            raise Exception("Missing dataset")
        c.dataset_id = row[0]

        if entity.get('error'):
            d = json.loads(entity.get('error'))
            c.first_failure = d.get('first_failure') or None
            c.last_success = d.get('last_success') or None

            c.url_redirected_to = d.get('url_redirected_to', '')
            c.reason = d.get('reason', '')
            c.failure_count = d.get('failure_count')

        return c

def init_tables(e):
    Base.metadata.create_all(e)
