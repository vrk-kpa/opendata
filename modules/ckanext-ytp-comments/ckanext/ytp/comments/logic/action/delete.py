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
