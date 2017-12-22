ckanext-ytp-main
================

Main CKAN extension for avoindata.fi

Installation
------------

Requires celery. See [ckanext-ytp-tasks](https://github.com/yhteentoimivuuspalvelut/ckanext-ytp-tasks).


This project requires files from [ytp-assets-common](https://github.com/yhteentoimivuuspalvelut/ytp-assets-common).

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-assets-common.git
    sudo cp ytp-assets-common/resources /var/www/resource


Installed as CKAN extension: ytp_user ytp_dataset ytp_organizations ytp_theme


    git clone https://github.com/yhteentoimivuuspalvelut/ckanext-ytp-main.git
    cd ckanext-ytp-user
    python setup.py develop # or install with pip

Add *ytp_user* *ytp_dataset* *ytp_organizations* *ytp_theme*  to CKAN plugins `/etc/ckan/default/production.ini` and restart the server.


[See how to install CKAN extensions.](http://docs.ckan.org/en/latest/extensions/tutorial.html#installing-the-extension)


Configuration
-------------

Add *ckanext.ytp.organizations.default_organization_name* and *ckanext.ytp.organizations.default_organization_title* variables to ckan ini file.

    ckanext.ytp.organizations.default_organization_name = "default_organization"
    ckanext.ytp.organizations.default_organization_title = "Default Organization"

Credits
-------

This extension uses parts of [ckanext-hierarchy](https://github.com/datagovuk/ckanext-hierarchy).

