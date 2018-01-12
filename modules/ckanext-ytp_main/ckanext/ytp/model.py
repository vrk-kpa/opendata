
# https://github.com/okfn/ckanext-datahub/blob/release-v2.0/ckanext/datahub/model/user_extra.py

import vdm.sqlalchemy
import vdm.sqlalchemy.stateful
from sqlalchemy import orm, types, Column, Table, ForeignKey

import ckan.model.user as user
import ckan.model.meta as meta
import ckan.model.types as _types
import ckan.model.domain_object as domain_object

import logging
from ckan import model
log = logging.getLogger(__name__)

__all__ = ['UserExtra', 'user_extra_table']

user_extra_table = Table('user_extra', meta.metadata,
                         Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                         Column('user_id', types.UnicodeText, ForeignKey('user.id')),
                         Column('key', types.UnicodeText),
                         Column('value', types.UnicodeText))

vdm.sqlalchemy.make_table_stateful(user_extra_table)


class UserExtra(vdm.sqlalchemy.StatefulObjectMixin, domain_object.DomainObject):
    pass


def setup():
    if model.user_table.exists() and not user_extra_table.exists():
        user_extra_table.create()
        log.debug('User extra table created')


def _create_extra(key, value):
    return UserExtra(key=unicode(key), value=value)


meta.mapper(UserExtra, user_extra_table,
            properties={'user': orm.relation(user.User, backref=orm.backref('_extras',
                                                                            collection_class=orm.collections.attribute_mapped_collection(u'key'),
                                                                            cascade='all, delete, delete-orphan'))},
            order_by=[user_extra_table.c.user_id, user_extra_table.c.key])

_extras_active = vdm.sqlalchemy.stateful.DeferredProperty('_extras', vdm.sqlalchemy.stateful.StatefulDict)
setattr(user.User, 'extras_active', _extras_active)
user.User.extras = vdm.sqlalchemy.stateful.OurAssociationProxy('extras_active', 'value', creator=_create_extra)
