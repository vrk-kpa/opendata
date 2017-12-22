from ckan.logic import check_access
from ckan.plugins import toolkit
from ckanext.ytp_tasks.model import YtpTaskSource, YtpTaskTables


def user_is_sysadmin(context):
    '''
        Checks if the user defined in the context is a sysadmin

        rtype: boolean
    '''
    model = context['model']
    user = context['user']
    user_obj = model.User.get(user)
    if not user_obj:
        raise toolkit.Objectpt.ObjectNotFound('User {0} not found').format(user)

    return user_obj.sysadmin


def auth_ytp_tasks_add(context, data_dict):
    if not user_is_sysadmin(context):
        return {'success': False, 'msg': toolkit._('Only sysadmins can add organization source')}
    else:
        return {'success': True}


def action_ytp_tasks_add(context, data_dict):
    YtpTaskTables.init()
    check_access('ytp_tasks_add', context, data_dict)

    task_id = data_dict['id']
    task = YtpTaskSource.get(task_id)
    new = False
    if not task:
        task = YtpTaskSource()
        new = True
    task.id = task_id
    task.task = data_dict['task']
    task.data = data_dict['data']
    task.frequency = data_dict['frequency']
    task.save()

    return {'success': True, 'new': new}
