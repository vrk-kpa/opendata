from setuptools import setup, find_packages
from ckanext.qa import __version__

setup(
    name='ckanext-qa',
    version=__version__,
    description="Quality Assurance plugin for CKAN",
    long_description="""
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Open Knowledge Foundation',
    author_email='info@okfn.org',
    url='http://ckan.org/wiki/Extensions',
    license='mit',
    packages=find_packages(exclude=['tests']),
    namespace_packages=['ckanext', 'ckanext.qa'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'celery>=2.3.3',
        'kombu-sqlalchemy>=1.1.0',
        'SQLAlchemy>=0.6.6',
        'requests==0.6.4',
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    entry_points=\
    """
    [paste.paster_command]
    qa=ckanext.qa.commands:QACommand

    [ckan.plugins]
    qa=ckanext.qa.plugin:QAPlugin
    """,
)

