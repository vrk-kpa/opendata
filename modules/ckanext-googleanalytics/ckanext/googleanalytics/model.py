import uuid
from datetime import datetime,timedelta

from sqlalchemy import Column
from sqlalchemy import types, func
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

class PackageStats(Base):
    """ 
    Contains stats for package (datasets)
    for GA tasks run against them
    Stores number of visits per all dates for each package.
    """
    __tablename__ = 'package_stats'

    package_id = Column(types.UnicodeText, nullable=False, index=True, primary_key=True)
    visit_date = Column(types.DateTime, default=datetime.now, primary_key=True)
    visits = Column(types.Integer)
   
    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.package_id == id).first()

    @classmethod
    def update_visits(cls, item_id, visit_date, visits):
        '''
        Updates the number of visits for a certain package_id 
        or creates a new one if it is the first visit for a certain date

        :param item_id: package_id
        :param visit_date: visit date to be updated
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        package = model.Session.query(cls).filter(cls.package_id == item_id).filter(cls.visit_date == visit_date).first()
        if package is None:
            package = PackageStats(package_id=item_id, visit_date=visit_date, visits=visits)
            model.Session.add(package)
        else:
            package.visits = visits

        log.debug("Number of visits for date: %s updated for package id: %s",visit_date,item_id)
        model.Session.flush()
        return True

    @classmethod
    def get_package_name_by_id(cls, package_id):
        package = model.Session.query(model.Package).filter(model.Package.id == package_id).first()
        pack_name = []
        if package is not None:
            pack_name = package.name
        return pack_name

    @classmethod
    def get_last_visits_by_id(cls, resource_id, num_days=30):
        start_date = datetime.now() - timedelta(num_days)
        package_visits = model.Session.query(cls).filter(cls.package_id == resource_id).filter(cls.visit_date >= start_date).all()
        #Returns the total number of visits since the beggining of all times
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.package_id == resource_id).scalar()
        visits = []

        if total_visits is not None:
            visits = PackageStats.convert_to_dict(package_visits, total_visits)

        return visits
    
                          
