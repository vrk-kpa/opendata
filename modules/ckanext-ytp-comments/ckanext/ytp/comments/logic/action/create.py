import datetime
import ckanext.ytp.comments.model as comment_model
import ckanext.ytp.comments.util as util
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
    users = comment_model.CommentSubscription.get_subscribers(package.id)

    if users:
        for user in users:
            log.debug("Sending comment notification mail now to:" + str(user.name))
            util.send_comment_notification_mail(user, package, cmt)

    return cmt.as_dict()

def add_comment_subscription(context, data_dict):
    model = context['model']
    user = context['user']
    package = context['package']

    userobj = model.User.get(user)

    dataset_id = package.id
    user_id = userobj.id

    # only logged in user with dataset rights can subscribe
    logic.check_access("add_comment_subscription", context, data_dict)

    if not userobj.id:
        raise logic.ValidationError("A valid user is required.")
    if not package.id:
        raise logic.ValidationError("A valid dataset is required.")

    scrn = comment_model.CommentSubscription.create(dataset_id, user_id)

    if not scrn:
        raise logic.ValidationError("Given dataset-user pair already exists in the database.")

    log.debug("Successfully added comment subscription for user {user_id} in dataset {dataset_id}"
              .format(user_id=user_id, dataset_id=dataset_id))
