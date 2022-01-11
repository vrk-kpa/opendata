import pytest
from ckan import model as ckan_model

from ckanext.ytp_recommendation import model
from ckanext.ytp_recommendation.tests import factories as ytp_factories


@pytest.mark.usefixtures('clean_db', 'clean_recommendation_table')
class TestRecommendationModel(object):
    def test_create_recommendation_with_package(self):
        ip = ytp_factories.get_ip_address()
        user = ytp_factories.get_or_create_user_object()
        package = ytp_factories.get_or_create_package_object()

        model.Recommendation.create_package_recommendation(package.id, ip, user.id)

        assert ckan_model.Session.query(model.Recommendation).count() == 1
        assert ckan_model.Session.query(model.Recommendation).first().package_id == package.id
        assert ckan_model.Session.query(model.Recommendation).first().user_id == user.id
        assert ckan_model.Session.query(model.Recommendation).first().ip_address == ip

    def test_get_recommendations_for_package(self):
        package = ytp_factories.get_or_create_package_object()
        user = ytp_factories.get_or_create_user_object()
        ip = ytp_factories.get_ip_address()

        model.Recommendation.create_package_recommendation(package.id, ip, user.id)

        assert len(model.Recommendation.get_package_recommendations(package.id)) == 1
        assert model.Recommendation.get_package_recommendations(package.id)[0].package_id == package.id

    def test_get_recommendation_count_for_user(self):
        ip = ytp_factories.get_ip_address()
        user = ytp_factories.get_or_create_user_object()
        package = ytp_factories.get_or_create_package_object()

        model.Recommendation.create_package_recommendation(package.id, ip, user.id)

        assert model.Recommendation.get_package_recommendations_count_for_user(
            ip,
            package.id,
            user.id,
        ) == 1
