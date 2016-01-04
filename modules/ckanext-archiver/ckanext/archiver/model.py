import uuid
from datetime import datetime

from sqlalchemy import Column, MetaData
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model
from ckan.lib import dictization

log = __import__('logging').getLogger(__name__)

Base = declarative_base()


def make_uuid():
    return unicode(uuid.uuid4())

metadata = MetaData()


# enum of all the archival statuses (singleton)
# NB Be very careful changing these status strings. They are also used in
# ckanext-qa tasks.py.
class Status:
    _instance = None

    def __init__(self):
        not_broken = {
            # is_broken = False
            0: 'Archived successfully',
        }
        broken = {
            # is_broken = True
            10: 'URL invalid',
            11: 'URL request failed',
            12: 'Download error',
        }
        not_sure = {
            # is_broken = None i.e. not sure
            21: 'Chose not to download',
            22: 'Download failure',
            23: 'System error during archival',
        }
        self._by_id = dict(not_broken, **broken)
        self._by_id.update(not_sure)
        self._by_text = dict((value, key)
                             for key, value in self._by_id.iteritems())

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def by_text(cls, status_txt):
        return cls.instance()._by_text[status_txt]

    @classmethod
    def by_id(cls, status_id):
        return cls.instance()._by_id[status_id]

    @classmethod
    def is_status_broken(cls, status_id):
        if status_id == 0:
            return False
        elif status_id < 20:
            return True
        else:
            return None  # not sure

    @classmethod
    def is_ok(cls, status_id):
        return status_id == 0

broken_enum = {True: 'Broken',
               None: 'Not sure if broken',
               False: 'Downloaded OK'}


class Archival(Base):
    """
    Details of the archival of resources. Has the filepath for successfully
    archived resources. Basic error history provided for unsuccessful ones.
    """
    __tablename__ = 'archival'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    package_id = Column(types.UnicodeText, nullable=False, index=True)
    resource_id = Column(types.UnicodeText, nullable=False, index=True)
    resource_timestamp = Column(types.DateTime)  # key to resource_revision

    # Details of the latest archival attempt
    status_id = Column(types.Integer)
    is_broken = Column(types.Boolean)  # Based on status_id. None = not sure
    reason = Column(types.UnicodeText)  # Extra detail explaining the status (cannot be translated)
    url_redirected_to = Column(types.UnicodeText)

    # Details of last successful archival
    cache_filepath = Column(types.UnicodeText)
    cache_url = Column(types.UnicodeText)
    size = Column(types.BigInteger, default=0)
    mimetype = Column(types.UnicodeText)
    hash = Column(types.UnicodeText)

    # History
    first_failure = Column(types.DateTime)
    last_success = Column(types.DateTime)
    failure_count = Column(types.Integer, default=0)

    created = Column(types.DateTime, default=datetime.now)
    updated = Column(types.DateTime)

    def __repr__(self):
        broken_details = '' if not self.is_broken else \
                         ('%d failures' % self.failure_count)
        package = model.Package.get(self.package_id)
        package_name = package.name if package else '?%s?' % self.package_id
        return '<Archival %s /dataset/%s/resource/%s %s>' % \
            (broken_enum[self.is_broken], package_name, self.resource_id,
             broken_details)

    @classmethod
    def get_for_resource(cls, resource_id):
        '''Returns the archival for the given resource, or if it doens't exist,
        returns None.'''
        return model.Session.query(cls).filter(cls.resource_id==resource_id).first()

    @classmethod
    def get_for_package(cls, package_id):
        '''Returns the archivals for the given package. May not be any if the
        package has no resources or has not been archived. It checks the
        resources are not deleted.'''
        return model.Session.query(cls) \
                    .filter(cls.package_id==package_id) \
                    .join(model.Resource, cls.resource_id==model.Resource.id) \
                    .filter(model.Resource.state=='active') \
                    .all()

    @classmethod
    def create(cls, resource_id):
        c = cls()
        c.resource_id = resource_id

        # Find the package_id for the resource.
        dataset = model.Session.query(model.Package)
        if hasattr(model, 'ResourceGroup'):
            # earlier CKANs had ResourceGroup
            dataset = dataset.join(model.ResourceGroup)
        dataset = dataset \
            .join(model.Resource) \
            .filter_by(id=resource_id) \
            .one()
        c.package_id = dataset.id
        return c

    @property
    def status(self):
        if self.status_id is None:
            return None
        return Status.by_id(self.status_id)

    def as_dict(self):
        context = {'model': model}
        archival_dict = dictization.table_dictize(self, context)
        archival_dict['status'] = self.status
        archival_dict['is_broken_printable'] = broken_enum[self.is_broken]
        return archival_dict


def aggregate_archivals_for_a_dataset(archivals):
    '''Returns aggregated archival info for a dataset, given the archivals for
    its resources (returned by get_for_package).

    :param archivals: A list of the archivals for a dataset's resources
    :type archivals: A list of Archival objects
    :returns: Archival dict about the dataset, with keys:
                status_id
                status
                reason
                is_broken
    '''
    archival_dict = {'status_id': None, 'status': None,
                     'reason': None, 'is_broken': None}
    for archival in archivals:
        # status_id takes the highest id i.e. pessimistic
        # reason matches the status_id
        if archival_dict['status_id'] is None or \
                archival.status_id > archival_dict['status_id']:
            archival_dict['status_id'] = archival.status_id
            archival_dict['reason'] = archival.reason

    if archivals:
        archival_dict['status'] = Status.by_id(archival_dict['status_id'])
        archival_dict['is_broken'] = \
            Status.is_status_broken(archival_dict['status_id'])
    return archival_dict


def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Archiver database tables are set-up')
