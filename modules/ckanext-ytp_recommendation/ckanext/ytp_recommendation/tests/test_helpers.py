from ckan.common import config

from ckanext.ytp_recommendation import helpers


class TestHelpers(object):
    def test_get_recaptcha_sitekey(self):
        sitekey = config.get('ckanext.ytp_recommendation.recaptcha_sitekey')
        assert helpers.get_ytp_recommendation_recaptcha_sitekey() == sitekey
