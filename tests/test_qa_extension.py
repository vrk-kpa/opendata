from paste.deploy import appconfig
import paste.fixture

from ckan.config.middleware import make_app
from ckan.tests import conf_dir, url_for, CreateTestData
from ckan.model import Session, Package

from ckanext.qa.lib.package_scorer import package_score
from ckanext.qa.lib import log
log.create_default_logger()

TEST_ARCHIVE_RESULTS_FILE = 'tests/test_archive_results.db'

class TestQAController:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'qa'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        CreateTestData.create()
                    
    @classmethod
    def teardown_class(self):
        CreateTestData.delete()
            
    def test_index(self):
        url = url_for('qa')
        response = self.app.get(url)
        assert 'Quality Assurance' in response, response
        
    def test_packages_with_broken_resource_links(self):
        url = url_for('qa_package_action', action='broken_resource_links')
        response = self.app.get(url)
        assert 'broken resource.' in response, response
        
    def test_package_openness_scores(self):
        # make sure the packages created by CreateTestData
        # have all the extra attributes we might expecting
        for p in Session.query(Package):
            package_score(p, TEST_ARCHIVE_RESULTS_FILE)
        url = url_for('qa_package_action', action='five_stars')
        response = self.app.get(url)
        assert 'openness scores' in response, response
