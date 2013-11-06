from setuptools import setup, find_packages

setup(
    name='ckanext-archiver',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'celery==2.4.2',
        'kombu==2.1.3',
        'kombu-sqlalchemy==1.1.0',
        'SQLAlchemy>=0.6.6',
        'requests==1.1.0',
        'messytables>=0.1.4',
        'flask==0.8'  # flask needed for tests
    ],
    author='Open Knowledge Foundation',
    author_email='info@okfn.org',
    description='Archive ckan resources',
    long_description='Archive ckan resources',
    license='MIT',
    url='http://ckan.org/wiki/Extensions',
    download_url='',
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
    [paste.paster_command]
    archiver = ckanext.archiver.commands:Archiver

    [ckan.plugins]
    archiver = ckanext.archiver.plugin:ArchiverPlugin

    [ckan.celery_task]
    tasks = ckanext.archiver.celery_import:task_imports
    '''
)
