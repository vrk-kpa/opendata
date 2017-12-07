import logging

import ckanext.ytp_comments.model as comment_model
from ckan.lib.base import abort
from ckan import logic

log = logging.getLogger(__name__)


def thread_show(context, data_dict):
    """
    Returns the content of a thread, based on a url. The url
    parameter MUST be present in the data_dict.
    with_deleted (boolean) - Also show deleted comments (requires sysadmin)
    offset (int) - The number of comments to offset in the threads comment list
    limit (int) - Total number of comments to return.
    """

    model = context['model']

    url = data_dict.get('url')
    id = data_dict.get('id')
    thread = None
    if url:
        thread = comment_model.CommentThread.from_url(url)

    if not thread and id:
        thread = comment_model.CommentThread.get(id)

    if not thread:
        return abort(404)

    data_dict['thread'] = thread
    # logic.check_access("thread_show", context, data_dict)

    # Dictize the thread and all the comments within it.
    thread_dict = thread.as_dict()
    # Add the top level comments from the thread in order to the following list.
    comments = model.Session.query(comment_model.Comment). \
        filter(comment_model.Comment.thread_id == thread.id)

    # Add more filters based on whether we want comments of a certain state,
    # or spam comments etc.
    if context.get('approved_only') is True:
        comments = comments.filter(comment_model.Comment.approval_status ==
                                   comment_model.COMMENT_APPROVED)

    if context.get('with_deleted') is not True:
        # TODO: Restrict to sysadmin
        comments = comments.filter(comment_model.Comment.state == 'active')

    # We only want the top-level comments because sub-comments will be retrieved in the
    # c.as_dict call
    comments = comments.filter(comment_model.Comment.parent_id == None)  # noqa

    if isinstance(context.get('offset'), int):
        comments = comments.offset(int(context.get('offset')))

    if isinstance(context.get('limit'), int):
        comments = comments.limit(int(context.get('limit')))

    if context.get('with_deleted') is not True:
        thread_dict['comments'] = [
            c.as_dict() for c in comments.order_by('comment.creation_date asc').all()
        ]
    else:
        thread_dict['comments'] = [
            c.as_dict(only_active_children=False) for c in comments.order_by('comment.creation_date asc').all()
        ]

    return thread_dict


def comment_show(context, data_dict):
    id = logic.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(id)
    if not comment:
        abort(404)
    logic.check_access("comment_show", context, data_dict)
    data_dict['comment'] = comment

    return comment.as_dict()


def comment_count(context, data_dict):

    # For now everybody is allowed to view count
    # logic.check_access('comment_count', context, data_dict)
    url = data_dict.get('url')
    id = data_dict.get('id')
    count = None
    if url:
        count = comment_model.CommentThread.count_from_url(url)

    if count is None and id:
        count = comment_model.CommentThread.count(id)

    if count is None:
        return abort(404)

    return count
