from setuptools import setup, find_packages

version = '0.2'

setup(name='ckanext-ytp-dataset',
      version=version,
      description="YTP dataset form",
      long_description="""\
      """,
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Salum',
      author_email='salum.abdul-rahman@gofore.com',
      url='',
      license='AGPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['ckanext', 'ckanext.ytp', 'ckanext.ytp.dataset'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'polib'
      ],
      message_extractors={
          'ckanext': [
              ('**.py', 'python', None),
              ('ytp/dataset/templates/**.html', 'ckan', None)
          ]
      },
      entry_points='''
            [ckan.plugins]
            ytp_dataset=ckanext.ytp.dataset.plugin:YTPDatasetForm
            [ckan.celery_task]
            tasks = ckanext.ytp.dataset.celery_import:task_imports
            [paste.paster_command]
            ytp-facet-translations = ckanext.ytp.dataset.commands:YtpFacetTranslations
      ''',)
