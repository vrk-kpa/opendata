ytp-theme-drupal
================

Drupal theme for YTP

Setup
-----

- Download https://github.com/twbs/bootstrap/archive/v3.0.0.zip
- Extract package to this directory
- Rename bootstrap-3.0.0 to bootstrap.

This project requires files from [ytp-assets-common](https://github.com/yhteentoimivuuspalvelut/ytp-assets-common).

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-assets-common.git
    sudo cp ytp-assets-common/resources /var/www/resources

Map /var/www/resources to /resources on web server.

Install
-------

Install as Drupal theme.

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-theme-drupal.git <drupal-root>/sites/all/themes/ytp_theme
    cd <drupal-root>
    drush en -y ytp_theme
