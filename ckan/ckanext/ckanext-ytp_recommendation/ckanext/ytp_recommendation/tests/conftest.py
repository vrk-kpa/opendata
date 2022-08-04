import ckan.model as ckan_model
import pytest

from ckanext.ytp_recommendation import model


@pytest.fixture
def clean_recommendation_table():
    engine = ckan_model.meta.engine

    if engine.dialect.has_table(engine, model.Recommendation.__tablename__):
        ckan_model.Session.query(model.Recommendation).delete()
        ckan_model.Session.commit()
    else:
        model.init_tables(engine)
