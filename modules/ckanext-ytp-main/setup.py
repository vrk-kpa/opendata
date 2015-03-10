from setuptools import setup, find_packages

version = '0.3'

setup(
    name='ckanext-ytp-main',
    version=version,
    description="Avoindata main extension",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='AGPL3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'polib',
        'rdflib'
    ],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('ytp/*/templates/**.html', 'ckan', None),
            ('**.js', 'javascript', None)
        ]
    },
    entry_points='''
        [ckan.plugins]
        ytp_user=ckanext.ytp.user.plugin:YtpUserPlugin
        ytp_organizations=ckanext.ytp.organizations.plugin:YtpOrganizationsPlugin
        ytp_organizations_display=ckanext.ytp.organizations.plugin:YtpOrganizationsDisplayPlugin
        hri_harvester=ckanext.ytp.organizations.harvesters.hriharvester:HRIHarvester
        ytp_theme=ckanext.ytp.theme.plugin:YtpThemePlugin
        ytp_dataset=ckanext.ytp.dataset.plugin:YTPDatasetForm
        ytp_service=ckanext.ytp.service.plugin:YTPServiceForm

        [ckan.celery_task]
        tasks = ckanext.ytp.common.celery_import:task_imports

        [paste.paster_command]
        ytp-facet-translations = ckanext.ytp.dataset.commands:YtpFacetTranslations
    ''',
)
