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
        package = model.Session.query(cls).filter(cls.item_id == package_id).filter(cls.visit_date == visit_date).first()
        if package is None:
            package = PackageStats(package_id=item_id, visit_date=visit_date, visits=visits)
            model.Session.add(package)
        else:
            package.visits = visits

        log.debug("Number of visits for date: %s updated for package id: %s",visit_date,item_id)
        model.Session.flush()
        return True

    @classmethod
    def get_last_visits_by_id(cls, resource_id, num_days=30):
        start_date = datetime.now() - timedelta(num_days)
        package_visits = model.Session.query(cls).filter(cls.package_id == resource_id).filter(cls.visit_date >= start_date).all()
        #Returns the total number of visits since the beggining of all times
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.package_id == resource_id)
        
        visits = PackageStats.convert_to_dict(package_visits, total_visits)

        return visits
    

    @classmethod
    def get_top(cls, limit=20):
        # caveat emptor: the query below will not filter out private
        # or deleted datasets (TODO)
        package_stats = model.Session.query(cls).order_by(cls.visit_date.desc()).limit(limit).all()
        return PackageStats.convert_to_dict(package_stats,None)

    @classmethod
    def as_dict(cls,res):
        result = {}
        result['package_id'] = res.package_id
        result['visits'] = res.visits
        result['visit_date'] = res.visit_date
        return result

    @classmethod
    def convert_to_dict(cls,resource_stats, tot_visits):
        visits = []
        for resource in resource_stats:
            visits.append(PackageStats.as_dict(resource))
        result = {}
        if tot_visits is not None:
            result['tot_visits'] = tot_visits
            visits.append(result)
        return visits


class ResourceStats(Base):
    """ 
    Contains stats for resources associated to a certain dataset/package
    for GA tasks run against them
    Stores number of visits i.e. downloads per all dates for each package.
    """
    __tablename__ = 'resource_stats'

    resource_id = Column(types.UnicodeText, nullable=False, index=True, primary_key=True)
    visit_date = Column(types.DateTime, default=datetime.now, primary_key=True)
    visits = Column(types.Integer)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.resource_id == id).first()

    @classmethod
    def update_visits(cls, item_id, visit_date, visits):
        '''
        Updates the number of visits for a certain resource_id

        :param item_id: resource_id
        :param visit_date: last visit date
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        resource = model.Session.query(cls).filter(cls.resource_id == item_id).first()
        if resource is None:
            resource = ResourceStats(resource_id=item_id, visit_date=visit_date, visits=visits)
            model.Session.add(resource)
        else:
            resource.visits = visits
            resource.visit_date = visit_date

        log.debug("Number of visits updated for resource id: %s",item_id)
        model.Session.flush()
        return True


    @classmethod
    def get_last_visits_by_id(cls, resource_id, num_days=30):
        start_date = datetime.now() - timedelta(num_days)
        resource_visits = model.Session.query(cls).filter(cls.resource_id == resource_id).filter(cls.visit_date >= start_date).all()
        #Returns the total number of visits since the beggining of all times
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id == resource_id)
        visits = ResourceStats.convert_to_dict(resource_visits, total_visits)
        return visits

    @classmethod
    def get_latest_update_date(cls):
        result = model.Session.query(cls).order_by(cls.visit_date.desc()).first()
        if result is None:
            return None
        else:
            return result.visit_date
        

    @classmethod
    def get_top(cls, limit=20):
        resource_stats = model.Session.query(cls).order_by(cls.visit_date.desc()).limit(limit).all()
        return ResourceStats.convert_to_dict(resource_stats,None)

    @classmethod
    def as_dict(cls,res):
        result = {}
        result['resource_id'] = res.package_id
        result['visits'] = res.visits
        result['visit_date'] = res.visit_date
        return result

    @classmethod
    def convert_to_dict(cls,resource_stats, tot_visits):
        visits = []
        for resource in resource_stats:
            visits.append(ResourceStats.as_dict(resource))
        result = {}
        if tot_visits is not None:
            result['tot_visits'] = tot_visits
            visits.append(result)
        return visits

    @classmethod
    def get_last_visits_by_url(cls, url, num_days=30):
        resource = model.Session.query(model.Resource).filter(model.Resource.url == url).first()
        start_date = datetime.now() - timedelta(num_days)
        #Returns the total number of visits since the beggining of all times for the associated resource to the given url
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id == resource.id)
        resource_stats = model.Session.query(cls).filter(cls.resource_id == resource.id).filter(cls.visit_date >= start_date).all()
        visits = ResourceStats.convert_to_dict(resource_stats, total_visits)

        return visits
    

    @classmethod
    def get_last_visits_by_dataset_id(cls, package_id, num_days=30):
        #Fetch all resources associated to this package id
        subquery = model.Session.query(model.Resource.id).filter(model.Resource.package_id == package_id).subquery()

        start_date = datetime.now() - timedelta(num_days)
        resource_stats = model.Session.query(cls).filter(cls.resource_id.in_(subquery)).filter(cls.visit_date >= start_date).all()
        #TODO: missing url from resource
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id.in_(subquery))
        visits = ResourceStats.convert_to_dict(resource_stats, total_visits)

        return visits

def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Google analytics database tables are set-up')


