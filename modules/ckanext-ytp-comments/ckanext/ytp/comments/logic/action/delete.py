import logging
from pylons import config
from pylons.i18n import _

import ckan.logic as logic
import ckan.new_authz as new_authz
import ckan.lib.helpers as h
from ckan.lib.base import abort, c

import ckanext.ytp.comments.model as comment_model

log = logging.getLogger(__name__)

def comment_delete(context, data_dict):
    model = context['model']
    user = context['user']

    logic.check_access("comment_delete", context, data_dict)

    # Comment should either be set state=='deleted' if no children,
    # otherwise content should be set to withdrawn text
    id = logic.get_or_bust(data_dict, 'id')
    comment = comment_model.Comment.get(id)
    if not comment:
        abort(404)

    if len(comment.children) > 0:
        txt = config.get('ckan.comments.deleted.text', 'This message was deleted')
        comment.comment = txt
    else:
        comment.state = 'deleted'

    model.Session.add(comment)
    model.Session.commit()

    return {'success': True}