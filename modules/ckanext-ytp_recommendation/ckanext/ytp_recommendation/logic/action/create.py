import logging

import ckan.model as ckan_model
import ckan.plugins as p
from ckan.logic import ValidationError

from ckanext.ytp_recommendation import model

log = logging.getLogger(__name__)
c = p.toolkit.c


def create_recommendation(context, data_dict):
    '''Create recommendations only for users who have not given a recommendation for this package'''
    user_id = c.userobj.id if c.userobj else None
    ip_address = p.toolkit.request.environ.get('REMOTE_ADDR')
    package_id = data_dict.get('package_id')

    if not package_id:
        raise ValidationError('No package id supplied.')
    if not ip_address:
        raise ValidationError('No ip address supplied.')

    package_exists = ckan_model.Session.query(
        ckan_model.Package).filter_by(id=package_id).first() is not None
    if not package_exists:
        raise ValidationError('Package does not exist.')

    user_can_recommend = p.toolkit.get_action('user_can_recommend')(context, data_dict)
    if user_can_recommend:
        model.Recommendation.create_package_recommendation(package_id, ip_address, user_id)

    return len(model.Recommendation.get_package_recommendations(package_id))
