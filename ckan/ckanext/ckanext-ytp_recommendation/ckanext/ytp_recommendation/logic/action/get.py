import logging

import ckan.model as ckan_model
from ckan.logic import ValidationError
from ckan.plugins import toolkit
from ckanext.ytp_recommendation import model
import ipaddress

log = logging.getLogger(__name__)
c = toolkit.c


@toolkit.side_effect_free
def get_recommendation_count_for_package(context, data_dict):
    package_id = data_dict.get('package_id')

    if not package_id:
        raise ValidationError('No package id supplied.')

    package_exists = ckan_model.Session.query(
        ckan_model.Package).filter_by(id=package_id).first() is not None
    if not package_exists:
        raise ValidationError('Package does not exist.')

    return len(model.Recommendation.get_package_recommendations(package_id))


@toolkit.side_effect_free
def get_user_can_make_recommendation(context, data_dict):
    '''
    Check whether a user can recommend a package or not.
    '''

    '''
    Validate ip from server variables and return it
    '''
    def get_client_ip_address():
        # Fallback fields to check original client ip
        ip_fields = ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP']
        for field in ip_fields:
            ip_address = toolkit.request.environ.get(field)
            # Check that ip_address for given server-env is set
            if ip_address is not None:
                try:
                    # Validate ip address
                    if ipaddress.ip_address(str(ip_address)):
                        return ip_address
                except (ValueError):
                    pass

    ip_address = get_client_ip_address()

    user_id = c.userobj.id if c.userobj else None
    package_id = data_dict.get('package_id')

    if not package_id:
        raise ValidationError('No package id supplied.')
    if not ip_address:
        raise ValidationError('No ip address supplied.')

    package_exists = ckan_model.Session.query(
        ckan_model.Package).filter_by(id=package_id).first() is not None
    if not package_exists:
        raise ValidationError('Package does not exist.')

    return model.Recommendation.get_package_recommendations_count_for_user(
        ip_address, package_id, user_id) == 0
