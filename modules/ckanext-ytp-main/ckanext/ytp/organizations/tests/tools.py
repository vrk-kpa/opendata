import os


def get_organization_test_source():
    return "file://%s" % os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/organization.json')


def get_organization_harvest_test_source():
    return "file://%s" % os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/organization_harvest.json')
