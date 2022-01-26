import datetime
import uuid

import ckan.model as model
from sqlalchemy import Column, MetaData, or_, types
from sqlalchemy.ext.declarative import declarative_base

log = __import__('logging').getLogger(__name__)
Base = declarative_base()
metadata = MetaData()


def make_uuid():
    return unicode(uuid.uuid4())


class Recommendation(Base):
    __tablename__ = 'recommendation'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid, nullable=False)
    created_at = Column(types.DateTime, default=datetime.datetime.now, nullable=False)
    ip_address = Column(types.UnicodeText, nullable=False)

    package_id = Column(types.UnicodeText, nullable=False)
    user_id = Column(types.UnicodeText)

    @classmethod
    def get_package_recommendations(cls, package_id):
        '''Get all recommendations for a specific package'''
        return model.Session.query(cls).filter(cls.package_id == package_id).all()

    @classmethod
    def create_package_recommendation(cls, package_id, ip_address, user_id=None):
        recommendation = Recommendation(
            package_id=package_id,
            ip_address=ip_address,
            user_id=user_id,
        )

        model.Session.add(recommendation)
        model.repo.commit()

    @classmethod
    def get_package_recommendations_count_for_user(cls, ip_address, package_id, user_id=None):
        '''Get the amount of recommendations created by a specific user or IP address for a package'''
        return model.Session.query(cls).filter(
            or_(cls.user_id == user_id, cls.ip_address == ip_address),
            cls.package_id == package_id
        ).count()


def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Recommendation tables are initialized.')
