from setuptools import setup, find_packages

version = '0.2'

setup(
    name='ckanext-ytp-theme',
    version=version,
    description="YTP theme",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='salum-ar',
    author_email='',
    url='',
    license='AGPL3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp', 'ckanext.ytp.theme'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('ytp/theme/templates/**.html', 'ckan', None)
        ]
    },
    entry_points='''
        [ckan.plugins]
        ytp_theme=ckanext.ytp.theme.plugin:YtpThemePlugin
    ''',
)
