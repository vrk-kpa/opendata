import uuid
import datetime

from sqlalchemy import Column, MetaData, ForeignKey, func, UniqueConstraint, and_, or_, Enum
from sqlalchemy import types
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from ckan.plugins import toolkit
from ckan.lib.base import model, config

log = __import__('logging').getLogger(__name__)

Base = declarative_base()
metadata = MetaData()

COMMENT_APPROVED = "approved"
COMMENT_PENDING = "pending"


def make_uuid():
    return unicode(uuid.uuid4())


def acceptable_comment_on(objtype):
    return objtype in ['package']


class CommentThread(Base):
    """
    Represents a thread, or in this particular case a collection of
    comments against a CKAN object.  This is the container for the
    """
    __tablename__ = 'comment_thread'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    url = Column(types.UnicodeText)
    creation_date = Column(types.DateTime, default=datetime.datetime.now)
    locked = Column(types.Boolean, default=False)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def clean_url(cls, incoming):
        """
        We are only interested in the path, so we will strip out
        everything else
        """
        from urlparse import urlparse
        parsed = urlparse(incoming)

        # Perhaps check on acceptable_comment_on()?

        return parsed.path

    @classmethod
    def from_url(cls, threadurl):
        u = cls.clean_url(threadurl)

        # Look for CommentThread for that URL or create it.
        thread = model.Session.query(cls). \
            filter(cls.url == u).first()
        if not thread:
            thread = cls(url=u)
            model.Session.add(thread)
            model.Session.commit()

        return thread

    @classmethod
    def count_from_url(cls, threadurl):

        u = cls.clean_url(threadurl)

        # Look for CommentThread for that URL or return 0
        thread = model.Session.query(cls). \
            filter(cls.url == u).first()
        if not thread:
            return 0

        thread_dict = thread.as_dict()
        children = model.Session.query(
            Comment.id,
            Comment.parent_id,
            Comment.thread_id)\
            .filter(Comment.state == 'active')\
            .cte(name='children', recursive=True)

        children = children.union_all(
            model.Session.query(
                Comment.id,
                Comment.parent_id,
                Comment.thread_id
            )
            .filter(Comment.id == children.c.parent_id)
        )

        q = model.Session.query(func.count('*').label('comment_count'),
                                children.c.thread_id).group_by(children.c.thread_id).filter(children.c.parent_id == None).subquery()  # noqa
        t = model.Session.query(func.sum(q.c.comment_count)).group_by(q.c.thread_id).filter(q.c.thread_id == thread_dict['id'])

        count = t.scalar()

        if count:
            return count

        return 0

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def count(cls, id):

        thread = model.Session.query(cls).filter(cls.id == id).first()
        if not thread:
            return 0

        thread_dict = thread.as_dict()

        children = model.Session.query(
            Comment.id,
            Comment.parent_id,
            Comment.thread_id) \
            .filter(Comment.state == 'active')\
            .cte(name='children', recursive=True)

        children = children.union_all(
            model.Session.query(
                Comment.id,
                Comment.parent_id,
                Comment.thread_id
            )
            .filter(Comment.id == children.c.parent_id)
        )

        q = model.Session.query(func.count('*').label('comment_count'),
                                children.c.thread_id).group_by(children.c.thread_id).filter(children.c.parent_id == None).subquery()  # noqa
        t = model.Session.query(func.sum(q.c.comment_count)).group_by(q.c.thread_id).filter(q.c.thread_id == thread_dict['id'])

        count = t.scalar()

        if count:
            return count

        return 0

    @classmethod
    def get_or_create(cls, obj, id):
        """
        Retrieves the thread for the specified object if any exists. If
        no thread currently exists, one is created for that object.
        """
        thread = model.Session.query(cls). \
            filter(cls.comment_on == obj). \
            filter(cls.comment_on_id == id).first()
        if not thread:
            if not acceptable_comment_on(obj):
                return None
            thread = CommentThread(comment_on=obj, comment_on_id=id)
            model.Session.add(thread)
            model.Session.commit()
        return thread

    def as_dict(self):
        d = {}
        d['url'] = self.url
        d['locked'] = self.locked
        d['created'] = self.creation_date.isoformat()
        d['id'] = self.id
        return d


class Comment(Base):
    """
    A comment is a text block provided by a user against an object, or in this
    particular case a CommentThread (one per object).
    """
    __tablename__ = 'comment'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    parent_id = Column(types.UnicodeText, ForeignKey('comment.id'))
    children = relationship("Comment", lazy="joined", join_depth=10,
                            backref=backref('parent', remote_side=[id]),
                            order_by="asc(Comment.creation_date)")

    thread_id = Column(types.UnicodeText, ForeignKey('comment_thread.id'), nullable=True)
    user_id = Column(types.UnicodeText, ForeignKey(model.User.id), nullable=False)
    subject = Column(types.UnicodeText)
    comment = Column(types.UnicodeText)

    creation_date = Column(types.DateTime, default=datetime.datetime.now)
    modified_date = Column(types.DateTime)
    approval_status = Column(types.UnicodeText)

    state = Column(types.UnicodeText, default=u'active')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Auto-set some values based on configuration
        from pylons import config
        if toolkit.asbool(config.get('ckan.comments.moderation', 'true')):
            self.approval_status = COMMENT_PENDING
        else:
            # If user wants first comment moderated and the user who wrote this hasn't
            # got another comment, put it into moderation, otherwise approve
            if toolkit.asbool(config.get('ckan.comments.moderation.first_only', 'true')) and \
                    Comment.count_for_user(self.user, COMMENT_APPROVED) == 0:
                self.approval_status = COMMENT_PENDING
            else:
                self.approval_status = COMMENT_APPROVED

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    def as_dict(self, only_active_children=True):
        """
        Returns this model as a dictionary, including all child comments (as dicts) if
        if has any
        """
        name = 'anonymous'
        u = model.User.get(self.user_id)
        if u:
            name = u.fullname

        # Hack
        if name == config.get('ckan.site_id', 'ckan_site_user') or not name:
            name = 'anonymous'

        d = {}
        d['id'] = self.id
        d['user_id'] = self.user_id
        d['username'] = name
        d['subject'] = self.subject
        d['content'] = self.comment
        d['state'] = self.state
        d['thread_id'] = self.thread_id
        d['creation_date'] = self.creation_date.isoformat()
        if self.modified_date:
            d['modified_date'] = self.modified_date.isoformat()
        if only_active_children is True:
            d['comments'] = [c.as_dict() for c in self.children if c.state == 'active']
        else:
            d['comments'] = [c.as_dict() for c in self.children]
        return d

    @classmethod
    def count_for_user(cls, user, status):
        return model.Session.query(Comment) \
            .filter(Comment.approval_status == status) \
            .filter(Comment.user == user).count()


class CommentBlockedUser(Base):
    """
    A blocked user who is not allowed to post anymore because they have
    previously posted spam.
    """
    __tablename__ = 'comment_blocked'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    user_id = Column(types.UnicodeText, ForeignKey(model.User.id))
    blocked_by = Column(types.UnicodeText, ForeignKey(model.User.id))
    creation_date = Column(types.DateTime, default=datetime.datetime.now)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CommentSubscription(Base):
    """
    A single comment subscription object as a identifier / user_id pair
    Identifier can be a dataset_id or an organization_id

    """
    __tablename__ = 'comment_subscribers'

    # TODO: this is currently not working. Why?
    __table_args__ = (UniqueConstraint('identifier', 'user_id', name="_dataset_user_uc"),)

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    identifier = Column(types.UnicodeText)
    user_id = Column(types.UnicodeText)
    subscription_type = Column(Enum("dataset", "organization", name="subscription_type"))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, identifier, user_id):
        '''
        Get the comment subscriber matching the dataset and user id's

        :param identifier: dataset id
        :param user_id: user id
        :return: a CommentSubscription object or None
        '''

        return model.Session.query(cls).filter(and_(cls.identifier == identifier, cls.user_id == user_id)).first()

    @classmethod
    def get_subscribers(cls, package):
        '''
        Fetch all comment subscribers

        :param package: either dataset or organization package
        :return: a list of User objects
        '''

        # query dataset specific AND organization wide subscribers
        subscribers = model.Session.query(cls).filter(or_(cls.identifier == package.id, cls.identifier == package.owner_org))

        users = []
        if subscribers:
            for sub in subscribers:
                user = model.Session.query(model.User).get(sub.user_id)
                if user and user not in users:
                    users.append(user)

        return users

    @classmethod
    def create(cls, identifier, user_id, subscription_type="dataset"):
        '''
        Create a new CommentSubscription and commit it to database

        :param identifier:
        :param user_id:
        :return: a subscription object
        '''

        if CommentSubscription.get(identifier, user_id):
            return False

        sbscrn = CommentSubscription(identifier=identifier, user_id=user_id, subscription_type=subscription_type)
        model.Session.add(sbscrn)
        model.Session.commit()
        return sbscrn

    @classmethod
    def delete(cls, identifier, user_id):
        '''
        Delete a single CommentSubscription that matches the given parameters
        :param identifier: dataset id
        :param user_id: user id
        :return: True for a successful deletion, otherwise False
        '''
        sbscrn = model.Session.query(cls).filter(and_(cls.identifier == identifier, cls.user_id == user_id)).first()
        if sbscrn:
            model.Session.delete(sbscrn)
            model.Session.commit()
            return True
        return False


def init_tables():
    Base.metadata.create_all(model.meta.engine)
