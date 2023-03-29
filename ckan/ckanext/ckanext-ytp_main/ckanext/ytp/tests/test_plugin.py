# -*- coding: utf-8 -*-
from ckan import model, plugins
from ckan.plugins import toolkit

# TODO: Custom db-clean and init must be implemented as ckans default doesn't work with postgis
# For a reference ckanext-spatial has some kind of implementation for postgis
# @pytest.mark.usefixtures('clean_db')
class TestYtpDatasetPlugin():
    """ Test YtpDatsetPlugin class """

    def setup(self):
        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()

    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        context['auth_user_obj'] = model.User.get(admin_user['name'])
        return context

    def test_create_dataset(self):
        context = self._create_context()
        data_dict = {'name': 'test_dataset_1', 'title': 'test_title', 'title_translated': {'fi': "otsikko"},
                     'license_id': "licence_id", 'notes_translated': {'fi': "Test notes"},
                     'keywords': {'fi': ["tag1", "tag2"]},
                     'collection_type': 'Open Data', 'copyright_notice_translated': {'fi': 'test_notice'},
                     'maintainer': 'test_maintainer', 'maintainer_email': 'test@maintainer.org'}

        result = toolkit.get_action('package_create')(context, data_dict)

        assert result['name'] == 'test_dataset_1'
        test_dataset = toolkit.get_action('package_show')(context, {'id': 'test_dataset_1'})
        assert test_dataset.get('title_translated').get('fi') == 'otsikko'
        assert test_dataset.get('copyright_notice_translated').get('fi') == 'test_notice'
