from setuptools import setup, find_packages

version = '0.1'

setup(name='ckanext-ytp_drupal',
      version=version,
      description="Fetch data from Drupal database",
      long_description=""" """,
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['ckanext', 'ckanext.ytp_drupal'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      message_extractors={
          'ckanext/ytp_drupal': [
              ('**.py', 'python', None),
              ('templates/**.html', 'ckan', None)
          ]
      },
      entry_points="""
      [ckan.plugins]
      ytp_drupal=ckanext.ytp_drupal.plugin:YtpDrupalPlugin
      [ckan.celery_task]
      tasks = ckanext.ytp_drupal.celery_import:task_imports
      """)
