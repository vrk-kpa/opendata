from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import types
from ckan.model.meta import metadata, mapper, Session
from ckan.model.domain_object import DomainObject
from ckan.model.types import make_uuid
import logging

log = logging.getLogger(__name__)

MANUAL = "MANUAL"
HOURLY = "HOURLY"
DAILY = "DAILY"
WEEKLY = "WEEKLY"

UPDATE_FREQUENCIES = [MANUAL, HOURLY, DAILY, WEEKLY]


class YtpTaskDomainObject(DomainObject):
    key_attr = 'id'

    @classmethod
    def get(cls, key, default=None, attr=None):
        '''Finds a single entity in the register.'''
        if attr is None:
            attr = cls.key_attr
        kwds = {attr: key}
        o = cls.filter(**kwds).first()
        if o:
            return o
        else:
            return default

    @classmethod
    def filter(cls, **kwds):
        query = Session.query(cls).autoflush(False)
        return query.filter_by(**kwds)


class YtpTaskSource(YtpTaskDomainObject):
    pass


class YtpTaskTables(object):
    ytp_task_source_table = None

    @classmethod
    def create_tables(cls):
        cls.init()
        if not cls.ytp_task_source_table.exists():
            cls.ytp_task_source_table.create()
            log.debug("YTP-task tables created")
            return True
        else:
            log.debug("YTP-task tables already created")
            return False

    @classmethod
    def init(cls):
        if cls.ytp_task_source_table is not None:
            return
        cls.ytp_task_source_table = Table(
            'ytp_task_source', metadata,
            Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
            Column('active', types.Boolean, default=True),
            Column('task', types.UnicodeText, nullable=False),
            Column('data', types.UnicodeText, nullable=True),
            Column('frequency', types.UnicodeText),
        )

        mapper(YtpTaskSource, cls.ytp_task_source_table)
