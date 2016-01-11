from ckan.plugins import toolkit as pt
from ckanext.harvest import model as harvest_model

def user_is_sysadmin(context):
    '''
        Checks if the user defined in the context is a sysadmin

        rtype: boolean
    '''
    model = context.get('model',None)
    user = context.get('user',None)
    if not model or not user:
        return False

    user_obj = model.User.get(user)
    if not user_obj:
        raise pt.Objectpt.ObjectNotFound('User {0} not found').format(user)

    return user_obj.sysadmin

def _get_object(context, data_dict, name, class_name):
    '''
        return the named item if in the data_dict, or get it from
        model.class_name
    '''
    if not name in context:
        id = data_dict.get('id', None)
        obj = getattr(harvest_model, class_name).get(id)
        if not obj:
            raise pt.ObjectNotFound
    else:
        obj = context.get(name)
    return obj

def get_source_object(context, data_dict = {}):
    return _get_object(context, data_dict, 'source', 'HarvestSource')

def get_job_object(context, data_dict = {}):
    return _get_object(context, data_dict, 'job', 'HarvestJob')

def get_obj_object(context, data_dict = {}):
    return _get_object(context, data_dict, 'obj', 'HarvestObject')
