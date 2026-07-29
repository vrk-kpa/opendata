import pytest

pytest_plugins = [
    u'ckanext.harvest.tests.fixtures',
]

@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("harvest")
