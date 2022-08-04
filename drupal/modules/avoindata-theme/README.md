<!-- @file Instructions for subtheming using the Less Starterkit. -->
<!-- @defgroup sub_theming_less -->
<!-- @ingroup sub_theming -->
# Avoindata subtheme

The Drupal 8 theme used at avoindata.fi is built on [Drupal Bootstrap](https://www.drupal.org/project/bootstrap) 8.x-3.x base theme.

## Installation

Avoindata.fi uses Ansible to move this repository in Drupal's theme folder, and Drush to enable the subtheme and set it as default theme. The code can be found at [Opendata repository](https://github.com/vrk-kpa/opendata).

## ytp-assets-common

This theme should be used together with [ytp-assets-common](https://github.com/vrk-kpa/opendata/tree/master/modules/ytp-assets-common).

* Theme requires ytp-assets-common/src/less/variables.less to set variables used in both Drupal and CKAN
* Theme Less files are compiled to CSS using ytp-assets-common's Gulpfile

## Developing the theme

1. Edit Less files in this repo or ytp-assets-common/src/less/variables.less. Changes in other files shouldn't change this theme.
2. In your local environment, cd to ytp-assets-common and run `gulp` or `gulp drupal`. This compiles Less to CSS.
3. In your virtual environment, run `sudo python /vagrant/scripts/ytp-develop.py avoindata-drupal-theme`. You only need to run it once to link your local files.
4. You usually need to empty Drupal theme cache at https://10.10.10.10/fi/admin/config/development/performance before you see any changes.
