import logging
import ckan.logic as logic

from ckan.lib.base import abort

import ckanext.ytp.comments.model as comment_model

log = logging.getLogger(__name__)


def comment_delete(context, data_dict):
    model = context['model']

    logic.check_access("comment_delete", context, data_dict)

    # Comment should either be set state=='deleted' if no children,
    # otherwise content should be set to withdrawn text
    id = logic.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(id)
    if not comment:
        abort(404)

    comment.state = 'deleted'

    model.Session.add(comment)
    model.Session.commit()

    return {'success': True}

def remove_comment_subscription(context, data_dict):
    model = context['model']
    user = context['user']
    package = context['package']

    userobj = model.User.get(user)

    dataset_id = package.id
    user_id = userobj.id

    # only subscriber can unsubscribe
    logic.check_access("remove_comment_subscription", context, data_dict)

    # VALIDATE THE FIELDS HERE
    if not userobj.id:
        logic.ValidationError("A valid user is required.")
    if not package.id:
        logic.ValidationError("A valid dataset is required.")

    # CREATE THE OBJECT
    scrn = comment_model.CommentSubscription.delete(dataset_id, user_id)

    log.debug("DELETED SUBSCRIPTION")
