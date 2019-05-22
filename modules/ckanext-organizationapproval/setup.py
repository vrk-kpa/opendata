from setuptools import setup, find_packages  # Always prefer setuptools over distutils

setup(
    name='ckanext-organizationapproval',
    version='0.0.1',
    description="",
    long_description="""""",
    # The project's main homepage.
    url='https://github.com/vrk-kpa/ckanext-organizationapproval',

    # Author details
    author="",
    author_email="",
    # Choose your license
    license='AGPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],

    # What does your project relate to?
    keywords="",

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    namespace_packages=['ckanext'],

    install_requires=[],

    include_package_data=True,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points='''
        [ckan.plugins]
        organizationapproval=ckanext.organizationapproval.plugin:OrganizationApprovalPlugin
    ''',
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
