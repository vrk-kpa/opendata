import pytest
from ckan import model as ckan_model

import mock
from ckanext.ytp_recommendation.model import Recommendation
from ckanext.ytp_recommendation.tests import factories


@pytest.mark.usefixtures('clean_db', 'clean_recommendation_table')
class TestController(object):
    @mock.patch(
        'ckanext.ytp_recommendation.controller.validate_google_recaptcha',
        mock.MagicMock(return_value=True)
    )
    def test_submit_recommendation(self, app):
        package = factories.get_or_create_package_object()
        url = '/recommendations/submit/'
        response = None

        assert ckan_model.Session.query(Recommendation).count() == 0

        with app.flask_app.app_context():
            client = app.flask_app.test_client()
            response = client.post(url, data={'package-id': package.id})

        assert ckan_model.Session.query(Recommendation).count() == 1
        assert ckan_model.Session.query(Recommendation).first().package_id == package.id
        assert ckan_model.Session.query(Recommendation).first().ip_address == '127.0.0.1'
        assert ckan_model.Session.query(Recommendation).first().user_id is None
        assert response.status_code == 302

    def test_get_recommendation_count(self, app):
        package = factories.get_or_create_package_object()
        user = factories.get_or_create_user_object()
        ip_address = factories.get_ip_address()

        factories.create_and_get_recommendation(
            package_id=package.id,
            user_id=user.id,
            ip=ip_address
        )

        url = u'/recommendations/get/{}'.format(package.id)
        response = None

        with app.flask_app.app_context():
            client = app.flask_app.test_client()
            response = client.get(url)

        assert response.status_code == 200
        assert response.data == '{"recommendation_count": 1}'

    def test_check_user_cant_recommend(self, app):
        package = factories.get_or_create_package_object()
        user = factories.get_or_create_user_object()
        ip_address = factories.get_ip_address()

        factories.create_and_get_recommendation(
            package_id=package.id,
            user_id=user.id,
            ip=ip_address
        )

        url = u'/recommendations/check_user/{}'.format(package.id)
        response = None

        with app.flask_app.app_context():
            client = app.flask_app.test_client()
            response = client.get(url)

        assert response.status_code == 200
        assert response.data == '{"can_recommend": false}'

    def test_check_user_can_recommend(self, app):
        package = factories.get_or_create_package_object()

        url = u'/recommendations/check_user/{}'.format(package.id)
        response = None

        with app.flask_app.app_context():
            client = app.flask_app.test_client()
            response = client.get(url)

        assert response.status_code == 200
        assert response.data == '{"can_recommend": true}'
