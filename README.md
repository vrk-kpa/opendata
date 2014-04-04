ckanext-ytp-groups
==================

YTP group CKAN extension. Provides modification to groups and organizations.

Features
--------

- Unique title names for organizations
- Default organization for users

Install
-------

Requires celery. See [ckanext-ytp-tasks](https://github.com/yhteentoimivuuspalvelut/ckanext-ytp-tasks).

Installed as CKAN extension: ytp_organizations

[See how to install CKAN extensions.](http://docs.ckan.org/en/latest/extensions/tutorial.html#installing-the-extension)

Configuration
-------------

Add *ckanext.ytp.organizations.default_organization_name* and *ckanext.ytp.organizations.default_organization_title* variables to ckan ini file.

    ckanext.ytp.organizations.default_organization_name = "default_organization"
    ckanext.ytp.organizations.default_organization_title = "Default Organization"

Credits
-------

This extension uses parts of [ckanext-hierarchy](https://github.com/datagovuk/ckanext-hierarchy).
