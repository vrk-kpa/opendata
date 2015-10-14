import uuid
import datetime

from sqlalchemy import Column, MetaData, ForeignKey, func
from sqlalchemy import types
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from ckan.plugins import toolkit
from ckan.lib.base import model, config

log = __import__('logging').getLogger(__name__)
Base = declarative_base()
metadata = MetaData()

"""No need for CANCEL state. If a member cancels
a request the entire request is deleted from the database. """ 
REQUEST_PENDING = "pending"
REQUEST_ACCEPTED = "accepted"
REQUEST_REJECTED = "rejected"
REQUEST_DELETED = "deleted"

def make_uuid():
    return unicode(uuid.uuid4())

class MemberRequest(Base):
    """
    Represents a member request containing request date, handled date, 
    status (pending, approved,rejected) and language used by the member 
    so that a localized e-mail could be sent
    """
    __tablename__ = 'member_request'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    member_id = Column(types.UnicodeText, ForeignKey(model.User.id))
    organization_id = Column(types.UnicodeText, ForeignKey(model.Group.id))
    request_date = Column(types.DateTime, default=datetime.datetime.now)
    role = Column(types.UnicodeText)
    handling_date = Column(types.DateTime)
    language = Column(types.UnicodeText)
    status = Column(types.UnicodeText,default=u"pending")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def init_tables():
    Base.metadata.create_all(model.meta.engine)



