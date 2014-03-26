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

class QATask(Base):
    """
    Contains the latest results per dataset/resource for QA tasks
    run against them.
    """
    __tablename__ = 'qa_task'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    organization_id = Column(types.UnicodeText, nullable=False, index=True)
    dataset_id = Column(types.UnicodeText, nullable=False, index=True)
    resource_id = Column(types.UnicodeText, nullable=False, index=True)
    error = Column(types.UnicodeText)

    openness_score = Column(types.Integer)
    openness_score_reason = Column(types.UnicodeText)

    url = Column(types.UnicodeText, index=True)
    format = Column(types.UnicodeText)
    is_broken = Column(types.Boolean, index=True)
    archiver_status = Column(types.UnicodeText)
    created   = Column(types.DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        result = {}
        result['value'] = self.openness_score
        result['last_updated'] = self.created

        result['is_broken'] = self.is_broken
        result['format'] = self.format
        result['archiver_status'] = self.archiver_status
        result['reason'] = self.openness_score_reason

        # deprecated keys
        result['openness_score'] = self.openness_score
        result['openness_score_reason'] = self.openness_score_reason
        result['openness_updated'] = self.created
        return result

    @classmethod
    def get_for_resource(cls, resource_id):
        return model.Session.query(cls).filter(cls.resource_id==resource_id).first()

    @classmethod
    def create(cls, entity):
        from paste.deploy.converters import asbool
        # Get the existing entry for the resource, or create  new one
        # if it doesn't exist.
        c = cls.get_for_resource(entity.get('entity_id')) or cls()

        c.resource_id = entity.get('entity_id')
        c.created = entity.get('last_updated')

        # We need to find the dataset_id for the resource.
        q = """
            SELECT P.id, P.owner_org from package P
            INNER JOIN resource_group RG ON RG.package_id = P.id
            INNER JOIN resource R ON R.resource_group_id = RG.id
            WHERE R.id = '%s';
        """
        row = model.Session.execute(q % c.resource_id).first()
        c.organization_id = row[1]
        c.dataset_id = row[0]
        c.openness_score = int(entity.get('value', 0))

        if entity.get('error'):
            d = json.loads(entity.get('error'))
            c.is_broken = asbool(d.get('is_broken', False))
            c.format = d.get('format')
            c.archiver_status = d.get('archiver_status')
            c.openness_score_reason = d.get('reason')

        return c

def init_tables(e):
    Base.metadata.create_all(e)
