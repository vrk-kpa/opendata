from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-qa',
	version=version,
	description="Quality assurance plugin for CKAN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='CKAN',
	author_email='ckan@okfn.org',
	url='http://ckan.org/wiki/Extensions',
	license='mit',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.qa'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
        #
	],
	tests_require=[
		'nose',
		'mock',
	],
	test_suite = 'nose.collector',
	entry_points=\
	"""
    [ckan.plugins]
	# Add plugins here, eg
	qa=ckanext.qa:QA
	[paste.paster_command]
	package-scores = ckanext.qa.commands.package_score:PackageScore
	""",
)
