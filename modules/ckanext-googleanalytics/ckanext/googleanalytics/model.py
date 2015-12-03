import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model

import datetime

log = __import__('logging').getLogger(__name__)

Base = declarative_base()


def init_tables():
    Base.metadata.create_all(model.meta.engine)
    log.info('Google analytics database tables are set-up')

class PackageStats(Base):
    """ 
    Contains stats for package
    for GA tasks run against them
    """
    __tablename__ = 'package_stats'

    package_id = Column(types.UnicodeText, nullable=False, index=True)
    visits = Column(types.Integer)
    visits_date = Column(types.DateTime, default=datetime.datetime.now)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def update_visits(cls, package_id, visit_date, visits):
        '''
        Updates the number of visits for a certain package_id

        :param package_id: package_id
        :param visit_date: last visit date
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        package = model.Session.query(cls).filter(cls.package_id == package_id).first()
        if package is None:
            package = PackageStats(package_id=package_id, visit_date=visit_date, visits=visits)
            model.Session.add(package)
        else:
            package.visits = visits
            package.visit_date = visit_date

        log.debug("Number of visits updated for package id: %s",package_id)
        model.Session.flush()
        return True

    @classmethod
    def get_last_visits_by_id(cls, resource_id, num_days=30):
        model.Session.query(cls).filter(cls.resource_id == resource_id)
    q = """
        select visit_date, visits from package_stats, package
        where package.id = package_id
        and visit_date >= :date_filter
        union all
        select null, sum(visits) from package_stats, package
        where package.id = package_id
        and package.id = :id
    """
    result = model.Session.connection().execute(text(q), id=id, date_filter=datetime.datetime.now() - datetime.timedelta(30)).fetchall()

    if result == [(None, None)]:
        result = []
    return result

    @classmethod
    def get_top(limit=20):
        items = []
        # caveat emptor: the query below will not filter out private
        # or deleted datasets (TODO)
        q = model.Session.query(model.Package)
        connection = model.Session.connection()
        package_stats = get_table('package_stats')
        s = select([package_stats.c.package_id,
                    package_stats.c.visits,
                    package_stats.c.visit_date])\
                    .order_by(package_stats.c.visit_date.desc())
        res = connection.execute(s).fetchmany(limit)
        for package_id, visits, visit_date in res:
            package_dict = {}
            item = q.filter("package.id = '%s'" % package_id)
            if not item.count():
                continue
            package_dict['package'] = item.first()
            package_dict['recent'] = visits
            package_dict['ever'] = visit_date
            items.append(package_dict)
        return items




class ResourceStats(Base):
    """ 
    Contains stats for resource 
    for GA tasks run against them
    """
    __tablename__ = 'resource_stats'

    resource_id = Column(types.UnicodeText, nullable=False, index=True)
    visits = Column(types.Integer)
    visits_date = Column(types.DateTime, default=datetime.datetime.now)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def update_visits(cls, resource_id, visit_date, visits):
        '''
        Updates the number of visits for a certain resource_id

        :param resource_id: resource_id
        :param visit_date: last visit date
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        resource = model.Session.query(cls).filter(cls.resource_id == resource_id).first()
        if resource is None:
            resource = ResourceStats(resource_id=resource_id, visit_date=visit_date, visits=visits)
            model.Session.add(resource)
        else:
            resource.visits = visits
            resource.visit_date = visit_date

        log.debug("Number of visits updated for resource id: %s",resource_id)
        model.Session.flush()
        return True

    @classmethod
    def get_latest_update_date():
    q = """
        SELECT max(visit_date) from resource_stats
        """
    result = model.Session.connection().execute(text(q)).first()
    if result == [(None, None)]:
        result = []
    return result[0].date()


    @classmethod
    def get_last_visits_by_id(resource_id, num_days):
        '''
        Gets the number of visits for a certain resource_id for the last num_days

        :param resource_id: resource_id
        :param num_days: number of days to filter the data
        :return: resources matching this query
        '''

        q = """
            SELECT visit_date, visits FROM resource_stats, resource
            WHERE resource_id = resource.id
            AND resource.id = :id and visit_date >= :date_filter
            UNION ALL
            SELECT null, sum(visits) from resource_stats, resource
            WHERE resource_id = resource.id
            AND resource.id = :id
        """
        count = model.Session.connection().execute(text(q), id=id, date_filter=datetime.datetime.now() - datetime.timedelta(30)).fetchall()
        if count == [(None, None)]:
            count = []
        return count

    @classmethod
    def get_visits_by_url(url):
    q = """
        SELECT visit_date, visits FROM resource_stats, resource
        WHERE resource_id = resource.id
        AND resource.url = :url and visit_date >= :date_filter
        UNION ALL
        SELECT null, sum(visits) from resource_stats, resource
        WHERE resource_id = resource.id
        AND resource.url = :url
    """
    count = model.Session.connection().execute(text(q), url=url, date_filter=datetime.datetime.now() - datetime.timedelta(30)).fetchall()
    if count == [(None, None)]:
        count = []
    return count


    @classmethod
    def get_top(limit=20):
    items = []
    connection = model.Session.connection()
    resource_stats = get_table('resource_stats')
    s = select([resource_stats.c.resource_id,
                resource_stats.c.visits,
                resource_stats.c.visit_date])\
                .order_by(resource_stats.c.visit_date.desc())
    res = connection.execute(s).fetchmany(limit)
    for resource_id, visits, visit_date in res:
        resource_dict = {}
        item = model.Session.query(model.Resource)\
               .filter("resource.id = '%s'" % resource_id)
        if not item.count():
            continue
        resource_dict['resource'] = item.first()
        resource_dict['recent'] = visits
        resource_dict['ever'] = visit_date
        items.append(resource_dict)
    return items




def get_resource_visits_for_package_id(id):
    q = """
      select visit_date, visits, resource.url from resource_stats, resource, package
      where resource_stats.resource_id = resource.id
      and package.id = package_id
      and package.id = :id and visit_date >= :date_filter
      union all
      select null, sum(visits), null from resource_stats, resource, package
      where resource_stats.resource_id = resource.id
      and package.id = package_id
      and package.id = :id
    """
    result = model.Session.connection().execute(text(q), id=id, date_filter=datetime.datetime.now() - datetime.timedelta(30)).fetchall()
    if result == [(None, None)]:
        result = []
    return result




