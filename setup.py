from setuptools import setup, find_packages

version = '0.3'

setup(
    name='ckanext-ytp-user',
    version=version,
    description="Avoindata user extension",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='AGPL3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp', 'ckanext.ytp.user'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('ytp/user/templates/**.html', 'ckan', None)
        ]
    },
    entry_points='''
        [ckan.plugins]
        ytp_user=ckanext.ytp.user.plugin:YtpUserPlugin
    ''',
)
