import datetime
import ckanext.ytp_comments.model as comment_model
import ckanext.ytp_comments.util as util
from pylons import config
from ckan import logic
from pprint import pprint
import logging

log = logging.getLogger(__name__)


def comment_create(context, data_dict):
    pprint(data_dict)
    pprint(context)
    model = context['model']
    user = context['user']

    userobj = model.User.get(user)

    logic.check_access("comment_create", context, data_dict)

    # Validate that we have the required fields.
    if not all([data_dict.get('comment')]):
        raise logic.ValidationError("Comment text is required")

    thread_id = data_dict.get('thread_id')

    if not thread_id:
        url = data_dict.get('url')
        if url:
            thread = comment_model.CommentThread.from_url(url)
            thread_id = thread.id if thread else None

    if not thread_id:
        raise logic.ValidationError("Thread identifier or URL is required")

    # Cleanup the comment
    cleaned_comment = util.clean_input(data_dict.get('comment'))

    # Create the object
    cmt = comment_model.Comment(thread_id=thread_id,
                                comment=cleaned_comment)
    cmt.user_id = userobj.id
    cmt.subject = data_dict.get('subject', 'No subject')

    if 'creation_date' in context:
        cmt.creation_date = datetime.datetime.fromtimestamp(context['creation_date'])

    # Check if there is a parent ID and that it is valid
    # TODO, validity in this case includes checking parent is not
    # deleted.
    prt = data_dict.get('parent_id')
    if prt:
        parent = comment_model.Comment.get(prt)
        if parent:
            cmt.parent_id = parent.id

    # approval and spam checking removed

    model.Session.add(cmt)
    model.Session.commit()

    # Send a notification mail to subscribed users
    package = context['package']
    users = comment_model.CommentSubscription.get_subscribers(package)

    if users:
        for user in users:
            log.debug("Sending comment notification mail now to:" + str(user.name))
            util.send_comment_notification_mail(user.display_name, user.email, package, cmt)

    # Always send a notification mail to website admin
    admin_email = config.get("ckanext-comments.comment_notifications_admin_email", None)
    if admin_email:
        util.send_comment_notification_mail("Avoindata-admin", admin_email, package, cmt)

    return cmt.as_dict()


def add_comment_subscription_dataset(context, data_dict):
    model = context['model']
    user = context['user']
    dataset_id = data_dict['dataset_id']
    userobj = model.User.get(user)

    logic.check_access("add_comment_subscription", context, data_dict)

    _subscribe(dataset_id, userobj.id, "dataset")


def add_comment_subscription_org(context, data_dict):
    model = context['model']
    user = context['user']
    org_id = data_dict['organization_id']
    userobj = model.User.get(user)

    logic.check_access("add_comment_subscription", context, data_dict)

    _subscribe(org_id, userobj.id, "organization")


def _subscribe(identifier, user_id, subscription_type=None):

    if not user_id:
        raise logic.ValidationError("A valid user is required.")

    if subscription_type not in ["dataset", "organization"]:
        raise logic.ValidationError("subscription_type parameter must be either 'dataset' or 'organization'")
    if not identifier:
        if subscription_type == "dataset":
            raise logic.ValidationError("A valid dataset id is required.")
        elif subscription_type == "organization":
            raise logic.ValidationError("A valid organization id is required.")

    scrn = comment_model.CommentSubscription.create(identifier, user_id, subscription_type)

    if not scrn:
        raise logic.ValidationError("Given identifier-user pair already exists in the database.")

    log.debug(("Successfully added comment subscription for user {user_id} in " + subscription_type + " {identifier}")
              .format(user_id=user_id, identifier=identifier))
