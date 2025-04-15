<!-- @file Instructions for subtheming using the SCSS Starterkit. -->
<!-- @defgroup sub_theming_scss -->
<!-- @ingroup sub_theming -->
# Avoindata subtheme

The Drupal 8 theme used at avoindata.fi is built on [Drupal Bootstrap](https://www.drupal.org/project/bootstrap) 8.x-3.x base theme.

## opendata-assets

This theme should be used together with [opendata-assets](https://github.com/vrk-kpa/opendata/tree/master/opendata-assets).

* Theme requires opendata-assets/src/scss/variables.scss to set variables used in both Drupal and CKAN
* Theme SCSS files are compiled to CSS using opendata-assets's Gulpfile

## Developing the theme

1. Edit SCSS files in this repo or opendata-assets/src/scss/variables.scss. Changes in other files shouldn't change this theme.
2. In your local environment, cd to opendata-assets and run `gulp` or `gulp drupal`. This compiles SCSS to CSS.
3. You usually need to empty Drupal theme cache at http://localhost/fi/admin/config/development/performance before you see any changes.
