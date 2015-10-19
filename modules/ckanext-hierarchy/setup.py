from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-hierarchy',
	version=version,
	description="CKAN Organization hierarchy - templates and configuration",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='David Read',
	author_email='david.read@hackneyworkshop.com',
	url='',
	license='Affero General Public License (AGPL)',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.hierarchy'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
        hierarchy_display=ckanext.hierarchy.plugin:HierarchyDisplay
        hierarchy_form=ckanext.hierarchy.plugin:HierarchyForm
	""",
)
