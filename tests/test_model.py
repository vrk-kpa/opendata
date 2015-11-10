import ckanext.archiver.model as archiver_model
try:
    from ckan.tests.helpers import reset_db
    from ckan.tests import factories as ckan_factories
except ImportError:
    from ckan.new_tests.helpers import reset_db
    from ckan.new_tests import factories as ckan_factories
from ckan import model

Archival = archiver_model.Archival


class TestArchival(object):
    @classmethod
    def setup_class(cls):
        reset_db()
        archiver_model.init_tables(model.meta.engine)

    def test_create(self):
        dataset = ckan_factories.Dataset()
        res = ckan_factories.Resource(package_id=dataset['id'])
        archival = Archival.create(res['id'])
        assert isinstance(archival, Archival)
        assert archival.package_id == dataset['id']
