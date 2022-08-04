from setuptools import setup, find_packages

version = '0.0'

setup(
    name='ckanext-ytp_comments',
    version=version,
    description="",
    long_description='''
    ''',
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp_comments'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    message_extractors={
        'ckanext/ytp_comments': [
            ('**.py', 'python', None),
            ('templates/**.html', 'ckan', None),
            ('**.js', 'javascript', None)
        ]
    },
    entry_points='''
        [ckan.plugins]
        ytp_comments=ckanext.ytp_comments.plugin:YtpCommentsPlugin

        [paste.paster_command]
        initdb = ckanext.ytp_comments.command:InitDBCommand
    '''
)
