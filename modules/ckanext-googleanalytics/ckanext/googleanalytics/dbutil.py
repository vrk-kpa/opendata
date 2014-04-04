from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.model.authz import PSEUDO_USER__VISITOR
from ckan.lib.base import *

cached_tables = {}


def init_tables():
    metadata = MetaData()
    package_stats = Table('package_stats', metadata,
                          Column('package_id', String(60),
                                 primary_key=True),
                          Column('visits_recently', Integer),
                          Column('visits_ever', Integer))
    resource_stats = Table('resource_stats', metadata,
                           Column('resource_id', String(60),
                                  primary_key=True),
                           Column('visits_recently', Integer),
                           Column('visits_ever', Integer))
    metadata.create_all(model.meta.engine)


def get_table(name):
    if name not in cached_tables:
        meta = MetaData()
        meta.reflect(bind=model.meta.engine)
        table = meta.tables[name]
        cached_tables[name] = table
    return cached_tables[name]


def _update_visits(table_name, item_id, recently, ever):
    stats = get_table(table_name)
    id_col_name = "%s_id" % table_name[:-len("_stats")]
    id_col = getattr(stats.c, id_col_name)
    s = select([func.count(id_col)],
               id_col == item_id)
    connection = model.Session.connection()
    count = connection.execute(s).fetchone()
    if count and count[0]:
        connection.execute(stats.update()\
            .where(id_col == item_id)\
            .values(visits_recently=recently,
                    visits_ever=ever))
    else:
        values = {id_col_name: item_id,
                  'visits_recently': recently,
                  'visits_ever': ever}
        connection.execute(stats.insert()\
                           .values(**values))


def update_resource_visits(resource_id, recently, ever):
    return _update_visits("resource_stats",
                          resource_id,
                          recently,
                          ever)


def update_package_visits(package_id, recently, ever):
    return _update_visits("package_stats",
                          package_id,
                          recently,
                          ever)


def get_resource_visits_for_url(url):
    connection = model.Session.connection()
    count = connection.execute(
        text("""SELECT visits_ever FROM resource_stats, resource
        WHERE resource_id = resource.id
        AND resource.url = :url"""), url=url).fetchone()
    return count and count[0] or ""


def get_top_packages(limit=20):
    items = []
    authorizer = Authorizer()
    q = authorizer.authorized_query(PSEUDO_USER__VISITOR,
                                    model.Package)
    connection = model.Session.connection()
    package_stats = get_table('package_stats')
    s = select([package_stats.c.package_id,
                package_stats.c.visits_recently,
                package_stats.c.visits_ever])\
                .order_by(package_stats.c.visits_recently.desc())
    res = connection.execute(s).fetchmany(limit)
    for package_id, recent, ever in res:
        item = q.filter("package.id = '%s'" % package_id)
        if not item.count():
            continue
        items.append((item.first(), recent, ever))
    return items


def get_top_resources(limit=20):
    items = []
    connection = model.Session.connection()
    resource_stats = get_table('resource_stats')
    s = select([resource_stats.c.resource_id,
                resource_stats.c.visits_recently,
                resource_stats.c.visits_ever])\
                .order_by(resource_stats.c.visits_recently.desc())
    res = connection.execute(s).fetchmany(limit)
    for resource_id, recent, ever in res:
        item = model.Session.query(model.Resource)\
               .filter("resource.id = '%s'" % resource_id)
        if not item.count():
            continue
        items.append((item.first(), recent, ever))
    return items
