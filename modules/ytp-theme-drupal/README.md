ytp-theme-drupal
================

Drupal theme for YTP

Setup
-----

This project requires files from [ytp-assets-common](https://github.com/yhteentoimivuuspalvelut/ytp-assets-common).

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-assets-common.git
    sudo cp ytp-assets-common/resources /var/www/resources

Install
-------

Install as Drupal theme.

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-theme-drupal.git <drupal-root>/sites/all/themes/ytp_theme
    cd <drupal-root>
    drush en -y ytp_theme
