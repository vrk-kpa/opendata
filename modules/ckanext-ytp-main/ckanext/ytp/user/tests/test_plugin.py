import paste.fixture
import pylons.test
from ckan.tests import TestCase
from ckan import model
from ckan.plugins import toolkit


class TestYtpUserPlugin(TestCase):
    """ Test YtpUserPlugin class """

    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)

    def setup(self):
        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()

    def teardown(self):
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        pass

    def _create_context(self, user_object):
        return {'model': model, 'session': model.Session, 'user': user_object.name, 'user_obj': user_object}

    def _create_user(self, name, fullname):
        user = model.User(name=name, email="test@example.com", fullname=fullname)
        model.Session.add(user)
        model.Session.commit()
        return user

    def test_user_update(self):
        user_object = self._create_user('tester', 'test tester')
        context = self._create_context(user_object)

        data_dict = {'id': user_object.name, 'email': user_object.email, 'fullname': user_object.fullname}
        toolkit.get_action('user_update')(context, data_dict)

        data_dict = {'id': user_object.name, 'email': user_object.email, 'fullname': user_object.fullname}
        data_dict_extras = {'facebook': 'http://example.com/facebook', 'job_title': 'tester', 'telephone_number': '+358 123 1234',
                            'image_url': 'http://example.com/me.png', 'linkedin': 'http://example.com/linkedin',
                            'twitter': 'http://example.com/twitter'}
        data_dict.update(data_dict_extras)

        from pprint import pprint
        pprint(data_dict)
        user_data = toolkit.get_action('user_update')(context, data_dict)
        user_show_data = toolkit.get_action('user_show')(context, {'id': user_object.name})
        updated_user = model.User.get('tester')

        for key, value in data_dict_extras.iteritems():
            self.assert_equal(user_data[key], value)
            self.assert_equal(user_show_data[key], value)
            self.assert_equal(updated_user.extras[key], value)
