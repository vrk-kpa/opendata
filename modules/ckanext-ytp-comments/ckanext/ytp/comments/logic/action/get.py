import logging

import ckanext.ytp.comments.model as comment_model
from ckan.lib.base import abort

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
    user = context['user']

    url = data_dict.get('url')
    id =  data_dict.get('id')
    thread = None
    if url:
        thread = comment_model.CommentThread.from_url(url)

    if not thread and id:
        thread = comment_model.CommentThread.get(id)

    if not thread:
        return abort(404)

    data_dict['thread'] = thread
    #logic.check_access("thread_show", context, data_dict)

    # Dictize the thread and all the comments within it.
    thread_dict = thread.as_dict()

    # Add the top level comments from the thread in order to the following list.
    comments = model.Session.query(comment_model.Comment). \
        filter(comment_model.Comment.thread_id==thread.id)

    # Add more filters based on whether we want comments of a certain state,
    # or spam comments etc.
    if context.get('approved_only') == True:
        comments = comments.filter(comment_model.Comment.approval_status ==
                                   comment_model.COMMENT_APPROVED)

    if context.get('with_deleted') != True:
        # TODO: Restrict to sysadmin
        comments = comments.filter(comment_model.Comment.state=='active')

    # We only want the top-level comments because sub-comments will be retrieved in the
    # c.as_dict call
    #comments = comments.filter(comment_model.Comment.parent_id == None)

    if isinstance(context.get('offset'),int):
        comments = comments.offset(int(context.get('offset')))

    if isinstance(context.get('limit'), int):
        comments = comments.limit(int(context.get('limit')))

    thread_dict['comments'] = [
        c.as_dict() for c in comments.order_by('comment.creation_date asc').all()
    ]

    return thread_dict
