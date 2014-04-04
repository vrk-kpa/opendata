from setuptools import setup, find_packages

version = '0.1'

setup(
    name='ckanext-drupal7',
    version=version,
    description="Drupal User Integration",
    long_description="""\
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Toby dacre',
    author_email='toby.dacre@okfn.org',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.drupal7'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points=\
    """
    [ckan.plugins]

    drupal7=ckanext.drupal7.plugin:Drupal7Plugin
    """,
)
