import httplib
import json
import urllib

import ckan.logic as logic
import ckan.model as model
import ckan.plugins as p
from ckan.common import config
from ckan.lib.base import h
from flask import Blueprint, request

c = p.toolkit.c
log = __import__('logging').getLogger(__name__)
bp_recommendations = Blueprint('recommendations_blueprint', __name__, url_prefix='/recommendations')


def get_blueprints():
    return [
        bp_recommendations,
    ]


@bp_recommendations.route('/submit/', methods=['POST'])
def submit_recommendation():
    recaptcha_response = request.form.get('g-recaptcha-response')
    package_id = request.form.get('package-id')
    package = model.Session.query(model.Package).get(package_id)

    data_dict = {'package_id': package_id}
    context = {'model': model}

    validate_google_recaptcha(recaptcha_response)

    p.toolkit.get_action('create_recommendation')(context, data_dict)

    response = h.redirect_to(controller='package', action='read', id=package.name)
    response.location = response.location + '?nocache=true'

    return response


@bp_recommendations.route('/get/<string:package_id>', methods=['GET'])
def get_recommendation_count_for_package(package_id):
    count = p.toolkit.get_action('get_recommendation_count')({}, {'package_id': package_id})
    return json.dumps({'recommendation_count': count})


@bp_recommendations.route('/check_user/<string:package_id>', methods=['GET'])
def check_user(package_id):
    data_dict = {'package_id': package_id}
    can_recommend = p.toolkit.get_action('user_can_recommend')({}, data_dict)
    return json.dumps({'can_recommend': can_recommend})


def validate_google_recaptcha(recaptcha_response):
    if not recaptcha_response:
        raise logic.ValidationError('Google reCaptcha response was empty.')

    response_data_dict = {}
    try:
        connection = httplib.HTTPSConnection('google.com')
        params = urllib.urlencode({
            'secret': config.get('ckanext.ytp_recommendation.recaptcha_secret'),
            'response': recaptcha_response,
            'remoteip': p.toolkit.request.environ.get('REMOTE_ADDR')
        })
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        connection.request('POST', '/recaptcha/api/siteverify', params, headers)
        response_data_dict = json.loads(connection.getresponse().read())
        connection.close()

        if response_data_dict.get('success') is not True:
            raise logic.ValidationError('Google reCaptcha validation failed')
    except Exception:
        log.error('Connection to Google reCaptcha API failed')
        raise logic.ValidationError('Connection to Google reCaptcha API failed, unable to validate captcha')
