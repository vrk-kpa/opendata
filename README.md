ckanext-ytp-theme
=================

CKAN Theme Extension for Yhteentoimivuuspalvelut

Installation
------------

This project requires files from [ytp-assets-common](https://github.com/yhteentoimivuuspalvelut/ytp-assets-common).

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-assets-common.git
    sudo cp ytp-assets-common/resources /var/www/resources

Map /var/www/resources to /resources on web server.

Install theme

    git clone https://github.com/yhteentoimivuuspalvelut/ckanext-ytp-theme.git
    cd ckanext-ytp-theme
    python setup.py develop # or install with pip

Add *ytp_theme* to CKAN plugins `/etc/ckan/default/production.ini` and restart the server.
