from nose.plugins.skip import SkipTest

from ckan.tests import conf_dir, url_for, CreateTestData, TestController
from ckan import model
from ckan.lib.dictization.model_dictize import package_dictize

class TestQAController(TestController):
    @classmethod
    def setup_class(cls):
        if model.engine_is_sqlite():
            raise SkipTest("Search not supported")
        CreateTestData.create()
                    
    @classmethod
    def teardown_class(self):
        CreateTestData.delete()
            
    def test_index(self):
        url = url_for('qa')
        response = self.app.get(url)
        assert 'Quality Assurance' in response, response
        
    def test_packages_with_broken_resource_links(self):
        url = url_for('qa_dataset_action', action='broken_resource_links')
        response = self.app.get(url)
        assert 'broken resource' in response, response
        
