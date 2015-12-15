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
	# requirements defined in pip-requirements.txt
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('qa/templates/**.html', 'ckan', None),
            ('**.js', 'javascript', None)
        ]
    },
    entry_points='''
    [paste.paster_command]
    qa=ckanext.qa.commands:QACommand

    [ckan.plugins]
    qa=ckanext.qa.plugin:QAPlugin

    [ckan.celery_task]
    tasks=ckanext.qa.celery_import:task_imports
    '''
)
