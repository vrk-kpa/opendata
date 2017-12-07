import logging
from ckan.common import _
from ckan import logic
import ckanext.ytp_comments.model as comment_model

log = logging.getLogger(__name__)


def comment_update(context, data_dict):
    user = context['user']
    model = context['model']

    userobj = model.User.get(user)

    if not userobj:
        log.debug("User is not logged in")
        return {'success': False, 'msg': _('You must be logged in to add a comment')}

    cid = logic.get_or_bust(data_dict, 'id')

    comment = comment_model.Comment.get(cid)
    if not comment:
        return {'success': False, 'msg': _('Comment does not exist')}

    if comment.user_id != userobj.id:
        return {'success': False, 'msg': _('User is not the author of the comment')}

    return {'success': True}
