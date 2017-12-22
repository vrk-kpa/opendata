from setuptools import setup, find_packages

version = '0.1'

setup(name='ckanext-ytp_tasks',
      version=version,
      description="Provides tasks for CKAN",
      long_description=""" """,
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['ckanext', 'ckanext.ytp_tasks'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [ckan.plugins]
      ytp_tasks=ckanext.ytp_tasks.plugin:YtpTasksPlugin
      [ckan.celery_task]
      tasks = ckanext.ytp_tasks.celery_import:task_imports
      [paste.paster_command]
      ytp-task-add = ckanext.ytp_tasks.commands:YtpTaskAdd
      ytp_tasks-initialize-database = ckanext.ytp_tasks.commands:YtpTaskInitDatabase
      ytp-task-execute-all = ckanext.ytp_tasks.commands:YtpTaskExecute
      """)
