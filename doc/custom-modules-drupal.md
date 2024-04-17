# Avoindata custom modules for Drupal 8

This document describes how to initialize and use our custom Drupal modules. Source code of modules can be found from [modules directory](https://github.com/vrk-kpa/opendata/tree/master/modules) and they have prefix of "avoindata-drupal". Some modules have a separate readme in their directory that might describe building or some other aspects of the module in more detail.

Many of the modules are being currently used only on the front page. The configuration in avoindata drupal theme specifies block modules that are being used in the front page and defines their placement (weight).

## Avoindata modules

Modules are installed and enabled within ansible Drupal role. Adding or removing a custom module requires changing the [custom_modules list](https://github.com/vrk-kpa/opendata/blob/master/ansible/roles/Ddupal/vars/main.yml)  that in Drupal role vars.


### Avoindata articles

Module for displaying a list of published avoindata articles. Module also allows users to filter the list with search functionality.

More information how to build the frontend for this module can be found from module specific [readme](https://github.com/vrk-kpa/opendata/blob/master/modules/avoindata-drupal-articles/README.md).

### Avoindata categories

Avoindata categories module. Displays list of CKAN categories (groups) in the frontpage.


### Avoindata events

Avoindata events module displays upcoming and past open data events and allows users to search these events from the list. One can also find a link to submit an event to the site from the avoindata events page.

### Avoindata footer

Avoindata footer module is used to display the site footer. The footer block also provides the footer via API (/api/footer) so that CKAN can also use the same footer as the Drupal side of the site.

### Avoindata guide

Avoindata guide module provides user guide for site users and displays the Avoindata Guide nodes. Templating for this module can be found under avoindata-drupal-theme.

### Avoindata header

Avoindata header module provides language switcher, main navigation menu links and option to search CKAN datasets. Similary to the footer module, this module is usable also via API (/api/header) and is being used by CKAN side of the site.

### Avoindata hero

Avoindata hero module is show as the "first" thing in the frontpage and it displays some statistics of the data within the site (number of datasets, organizations and applications). Hero module allows users to quickly search CKAN datasets, organizations and applications (redirect to CKAN site with search terms.). It also provides links to recent and popular datasets and to the application listing.

### Avoindata infobox

Avoindat infobox module displays three infoboxes on the frontpage of the site.

### Avoindata newsfeed

Avoindata newsfeed module displays five most recent news and events in user language. This Drupal block is being used on the frontpage of the site.

### Avoindata servicemessage

Avoindata servicemessage module is being used to show service messages (eg. scheduled downtimes for site updates). Adding service messages can be done via Drupal admin panel (Avoindata Servicemessage content type). When creating a service message, one must remember to add a service message for each site language (fi/en/sv).

### Avoindata theme

Avoindata theme module is based on the Drupal 8 boostrap theme. It contains Drupal specific configuration and template overrides. CSS (less) style related to the Drupal side can be found from [ytp-assets-common](https://github.com/vrk-kpa/opendata/tree/master/modules/ytp-assets-common/src/less/Drupal). Building styles is done with the gulp file found from the same module.

### Avoindata user

Avoindata user module modifies the way users are being validated by Drupal instance.
