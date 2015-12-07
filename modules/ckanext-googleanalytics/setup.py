from setuptools import setup, find_packages

version = '0.2'

setup(
    name='ckanext-googleanalytics',
    version=version,
    description="Add GA tracking and reporting to CKAN instance",
    long_description="""\
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Seb Bacon, Oscar Perez',
    author_email='seb.bacon@gmail.com, oscar.perez@gofore.com',
    url='http://ckan.org/wiki/Extensions',
    license='AGPL3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.googleanalytics'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
       # Requirements defined in pip-requirements.txt
    ],
    entry_points='''
    [paste.paster_command]
    loadanalytics = ckanext.googleanalytics.commands:LoadAnalytics
    initdb = ckanext.googleanalytics.commands:InitDB
    getauthtoken = ckanext.googleanalytics.commands:GetAuthToken

    [ckan.plugins]
    googleanalytics=ckanext.googleanalytics.plugin:GoogleAnalyticsPlugin
    '''
)
