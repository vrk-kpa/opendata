from setuptools import setup, find_packages
from ckanext.qa import __version__

setup(
    name='ckanext-qa',
    version=__version__,
    description='Quality Assurance plugin for CKAN',
    long_description='',
    classifiers=[],
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
        'celery==2.4.2',
        'kombu==2.1.3',
        'kombu-sqlalchemy==1.1.0',
        'SQLAlchemy>=0.6.6',
        'requests==1.1.0',
        'python-magic==0.4.3',
        'xlrd>=0.8.0',
        'messytables>=0.8',
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    entry_points='''
    [paste.paster_command]
    qa=ckanext.qa.commands:QACommand

    [ckan.plugins]
    qa=ckanext.qa.plugin:QAPlugin

    [ckan.celery_task]
    tasks=ckanext.qa.celery_import:task_imports
    ''',
)
