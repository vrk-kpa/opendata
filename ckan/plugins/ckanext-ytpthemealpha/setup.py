from setuptools import setup, find_packages
import sys, os

version = '0.1.3'

setup(
	name='ckanext-ytpthemealpha',
	version=version,
	description="YTP theme attempt",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='salum-ar',
	author_email='',
	url='',
	license='AGPL3',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.ytpthemealpha'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points='''
        [ckan.plugins]
        ytpthemealpha=ckanext.ytpthemealpha.plugin:YTPThemeAlphaPlugin
	# Add plugins here, eg
	# myplugin=ckanext.ytpthemealpha:PluginClass
	''',
)
