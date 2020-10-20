from setuptools import setup, find_packages

version = '0.3'

setup(
    name='ckanext-ytp_main',
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
    install_requires=[],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('ytp/templates/**.html', 'ckan', None),
            ('**.js', 'javascript', None)
        ]
    },
    entry_points='''
        [ckan.plugins]
        ytp_user=ckanext.ytp.plugin:YtpUserPlugin
        ytp_organizations=ckanext.ytp.plugin:YtpOrganizationsPlugin
        ytp_organizations_display=ckanext.ytp.plugin:YtpOrganizationsDisplayPlugin
        hri_harvester=ckanext.ytp.harvesters.hriharvester:HRIHarvester
        sixodp_harvester=ckanext.ytp.harvesters.sixodp_harvester:SixodpHarvester
        syke_harvester=ckanext.ytp.harvesters.syke_harvester:SYKEHarvester
        ytp_theme=ckanext.ytp.plugin:YtpThemePlugin
        ytp_dataset=ckanext.ytp.plugin:YTPDatasetForm
        ytp_spatial=ckanext.ytp.plugin:YTPSpatialHarvester
        ytp_report=ckanext.ytp.plugin:YtpReportPlugin
        ytp_restrict_category_creation_and_updating=ckanext.ytp.plugin:YtpRestrictCategoryCreationAndUpdatingPlugin
        ytp_ipermission_labels=ckanext.ytp.plugin:YtpIPermissionLabelsPlugin
        ytp_resourcestatus=ckanext.ytp.resourcestatusplugin:ResourceStatusPlugin
        ytp_harvesterstatus=ckanext.ytp.harvesterstatusplugin:HarvesterStatusPlugin
        opendata_group=ckanext.ytp.plugin:OpenDataGroupPlugin

        [ckan.celery_task]
        tasks = ckanext.ytp.celery_import:task_imports

        [paste.paster_command]
        ytp-facet-translations = ckanext.ytp.commands:YtpFacetTranslations
        ytp-dataset = ckanext.ytp.commands:ytp_dataset_group
        ytp-organization = ckanext.ytp.commands:ytp_org_group
        opendata-group = ckanext.ytp.commands:opendata_group
        opendata-harvest = ckanext.ytp.commands:opendata_harvest_group

        [ckan.rdf.profiles]
        avoindata_dcat_ap=ckanext.ytp.dcat:AvoindataDCATAPProfile
    ''',
)
