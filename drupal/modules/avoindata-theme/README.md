<!-- @file Instructions for subtheming using the Less Starterkit. -->
<!-- @defgroup sub_theming_less -->
<!-- @ingroup sub_theming -->
# Avoindata subtheme

The Drupal 8 theme used at avoindata.fi is built on [Drupal Bootstrap](https://www.drupal.org/project/bootstrap) 8.x-3.x base theme.

## Installation

Avoindata.fi uses Ansible to move this repository in Drupal's theme folder, and Drush to enable the subtheme and set it as default theme. The code can be found at [Opendata repository](https://github.com/vrk-kpa/opendata).

## opendata-assets

This theme should be used together with [opendata-assets](https://github.com/vrk-kpa/opendata/tree/master/opendata-assets).

* Theme requires opendata-assets/src/less/variables.less to set variables used in both Drupal and CKAN
* Theme Less files are compiled to CSS using opendata-assets's Gulpfile

## Developing the theme

1. Edit Less files in this repo or opendata-assets/src/less/variables.less. Changes in other files shouldn't change this theme.
2. In your local environment, cd to opendata-assets and run `gulp` or `gulp drupal`. This compiles Less to CSS.
3. You usually need to empty Drupal theme cache at http://localhost/fi/admin/config/development/performance before you see any changes.
