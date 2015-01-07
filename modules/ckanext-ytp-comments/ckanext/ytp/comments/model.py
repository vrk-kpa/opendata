from sqlalchemy import Table, Column, types, ForeignKey, orm

from ckan import model
from ckan.model.meta import metadata
from ckan.model.types import make_uuid

from ckan.model import Package

import ckan.model.meta as meta
import ckan.model.domain_object as domain_object

import logging

log = logging.getLogger(__name__)

__all__ = [
    'PackageComment', 'package_comment_table'
]

package_comment_table = None

def setup():
    if package_comment_table is None:
        define_comment_table()
        log.debug("Package Comment table defined in memory.")

    if model.package_table.exists():
        if not package_comment_table.exists():
            package_comment_table.create()
            log.debug("Package Comment table created.")
        else:
            log.debug("Package Comment table already exists.")

    else:
        log.debug("Package Comment table creation deferred.")


def define_comment_table():
    global  package_comment_table

    package_comment_table = Table("package_comment", metadata,
        Column("id", types.UnicodeText, primary_key=True, default=make_uuid),
        Column("package_id", types.UnicodeText, ForeignKey("package.id"), nullable=False),
        Column("user_id", types.UnicodeText, ForeignKey("user.id"), nullable=False),
        Column("reply_to", types.UnicodeText, ForeignKey("package_comment.id")),
        Column("date", types.DateTime)
    )

    meta.mapper(PackageComment, package_comment_table, properties={
        'package', orm.relation(Package, backref="package_comments")}
    )


class PackageComment(domain_object.DomainObject):
    @classmethod
    def get(cls, comment_id):
        return meta.Session.query(PackageComment).filter(PackageComment.id == comment_id).first()

