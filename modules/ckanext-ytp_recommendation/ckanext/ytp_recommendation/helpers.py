from ckan.common import config


def get_ytp_recommendation_recaptcha_sitekey():
    return config.get('ckanext.ytp_recommendation.recaptcha_sitekey')
