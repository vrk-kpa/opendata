from setuptools import setup, find_packages

version = '0.1'

setup(
    name='ckanext-ytp-organizations',
    version=version,
    description="Organization customization",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='Affero General Public License (AGPL)',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp'],
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    message_extractors={
        'ckanext/ytp/organizations': [
            ('**.py', 'python', None),
            ('templates/**.html', 'ckan', None)
        ]
    },
    include_package_data=True,
    entry_points="""
        [ckan.plugins]
        ytp_organizations=ckanext.ytp.organizations.plugin:YtpOrganizationsPlugin
        ytp_organizations_display=ckanext.ytp.organizations.plugin:YtpOrganizationsDisplayPlugin
        [ckan.celery_task]
        tasks = ckanext.ytp.organizations.celery_import:task_imports
    """,)
