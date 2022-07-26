import ckan.model as model
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base


log = __import__('logging').getLogger(__name__)
Base = declarative_base()


class MunicipalityBoundingBox(Base):
    '''
    Contains bbox data for every Finnish municipality
    '''
    __tablename__ = 'municipality_bounding_boxes'

    name = Column(types.UnicodeText, nullable=False, primary_key=True)
    lat_min = Column(types.UnicodeText, nullable=False)
    lat_max = Column(types.UnicodeText, nullable=False)
    lng_min = Column(types.UnicodeText, nullable=False)
    lng_max = Column(types.UnicodeText, nullable=False)

    @classmethod
    def bulk_save(cls, objects):
        model.Session.bulk_save_objects(objects)
        model.Session.commit()


def ytp_main_init_tables(engine):
    msg = 'Tables initialized: MunicipalityBoundingBox'
    Base.metadata.create_all(engine)
    log.info(msg)
