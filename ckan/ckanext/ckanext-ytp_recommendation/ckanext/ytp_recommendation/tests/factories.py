from ckan import model as ckan_model
from ckan.tests import factories as ckan_factories

from ckanext.ytp_recommendation import model


def get_recommendation(package_id=None, user_id=None, ip=None):
    ip = ip if ip else get_ip_address()
    package_id = package_id if package_id else get_or_create_package_object()
    user_id = user_id if user_id else get_or_create_user_object()

    return model.Recommendation(
        package_id=package_id,
        user_id=user_id,
        ip_address=ip,
    )


def create_and_get_recommendation(package_id=None, user_id=None, ip=None):
    recommendation = get_recommendation(package_id, user_id, ip)
    _save_to_database(recommendation)
    return recommendation


def get_user_object(name=None):
    user_data = ckan_factories.User()
    model_data = {
        'name': name if name else user_data.get('name'),
        'password': u'{}'.format(user_data.get('password')),
        'about': user_data.get('about'),
        'image_url': user_data.get('image_url'),
        'fullname': user_data.get('fullname'),
        'email': user_data.get('email'),
    }

    return ckan_model.User(**model_data)


def get_or_create_user_object(user=None):
    user_obj = user if user else get_user_object()

    obj_from_db = ckan_model.Session.query(ckan_model.User).filter(
        ckan_model.User.name == user_obj.name).first()
    if obj_from_db:
        return obj_from_db

    _save_to_database(user_obj)

    return user_obj


def get_package_object():
    package_data = ckan_factories.Dataset()
    model_data = {
        'name': package_data.get('name'),
        'title': package_data.get('title')
    }
    return ckan_model.Package(**model_data)


def get_or_create_package_object():
    package = get_package_object()

    obj_from_db = ckan_model.Session.query(ckan_model.Package).filter(
        ckan_model.Package.name == package.name).first()
    if obj_from_db:
        return obj_from_db

    _save_to_database(package)

    return package


def _save_to_database(obj):
    ckan_model.Session.add(obj)
    ckan_model.repo.commit()


def get_ip_address():
    return '127.0.0.1'
