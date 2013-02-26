from setuptools import setup, find_packages

setup(
    name='ckanext-archiver',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # Requirements defined in pip-requirements.txt
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
