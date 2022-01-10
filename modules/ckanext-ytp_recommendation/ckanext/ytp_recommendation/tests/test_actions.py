import pytest
from ckan.plugins import toolkit

from ckanext.ytp_recommendation.logic.action import create, get
from ckanext.ytp_recommendation.model import Recommendation
from ckanext.ytp_recommendation.tests import factories as ytp_factories


@pytest.mark.usefixtures('clean_db', 'clean_recommendation_table')
class TestGetActions(object):
    def test_get_user_can_make_recommendation_w_userobj(self, app):
        package = ytp_factories.get_or_create_package_object()
        user = ytp_factories.get_or_create_user_object()

        with app.flask_app.test_request_context('/'):
            with app.flask_app.app_context():
                toolkit.request.environ['REMOTE_ADDR'] = ytp_factories.get_ip_address()
                toolkit.c.userobj = user

                result = get.get_user_can_make_recommendation({}, {'package_id': package.id})
                assert result

                ytp_factories.create_and_get_recommendation(
                    user_id=user.id,
                    package_id=package.id,
                    ip=ytp_factories.get_ip_address())

                result = get.get_user_can_make_recommendation({}, {'package_id': package.id})
                assert not result

    def test_get_user_count_for_package(self):
        package = ytp_factories.get_or_create_package_object()
        user = ytp_factories.get_or_create_user_object()
        ip = ytp_factories.get_ip_address()

        data_dict = {'package_id': package.id}

        assert get.get_recommendation_count_for_package({}, data_dict) == 0

        ytp_factories.create_and_get_recommendation(package_id=package.id, ip=ip, user_id=user.id)

        assert get.get_recommendation_count_for_package({}, data_dict) == 1


@pytest.mark.usefixtures('clean_db', 'clean_recommendation_table')
class TestCreateActions(object):
    def test_create_recommendation_w_userbj(self, app):
        package = ytp_factories.get_or_create_package_object()
        user = ytp_factories.get_or_create_user_object()
        data_dict = {'package_id': package.id}

        with app.flask_app.test_request_context('/'):
            with app.flask_app.app_context():
                toolkit.request.environ['REMOTE_ADDR'] = ytp_factories.get_ip_address()
                toolkit.c.userobj = user

                recommendation_count = len(Recommendation.get_package_recommendations(package.id))
                assert recommendation_count == 0

                recommendation_count = create.create_recommendation({}, data_dict)
                assert recommendation_count == 1
