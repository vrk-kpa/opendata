import logging
import ckan.logic as logic

from ckan.lib.base import abort

import ckanext.ytp_comments.model as comment_model

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


def remove_comment_subscription_dataset(context, data_dict):
    model = context['model']
    user = context['user']
    package = context['package']

    userobj = model.User.get(user)

    dataset_id = package.id

    logic.check_access("remove_comment_subscription", context, data_dict)

    _unsubscribe(dataset_id, userobj.id, "dataset")


def remove_comment_subscription_org(context, data_dict):
    model = context['model']
    user = context['user']
    org_id = data_dict['organization_id']
    userobj = model.User.get(user)

    logic.check_access("remove_comment_subscription", context, data_dict)

    _unsubscribe(org_id, userobj.id, "organization")


def _unsubscribe(identifier, user_id, subscription_type=None):

    if not user_id:
        raise logic.ValidationError("A valid user is required.")

    if subscription_type not in ["dataset", "organization"]:
        raise logic.ValidationError("subscription_type parameter must be either 'dataset' or 'organization'")

    if not identifier:
        if subscription_type == "dataset":
            raise logic.ValidationError("A valid dataset id is required.")
        elif subscription_type == "organization":
            raise logic.ValidationError("A valid organization id is required.")

    comment_model.CommentSubscription.delete(identifier, user_id)

    log.debug(("Successfully deleted comment subscription for user {user_id} in " + subscription_type + " {identifier}")
              .format(user_id=user_id, identifier=identifier))
