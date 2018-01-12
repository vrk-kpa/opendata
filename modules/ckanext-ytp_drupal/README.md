ckanext-ytp-drupal
==================

This extension provides data utility methods from CKAN to Drupal. 

- service_alerts method for CKAN templates (h.service_alerts())

Installation
------------

Installed as CKAN extension: ytp_drupal

[See how to install CKAN extensions.](http://docs.ckan.org/en/latest/extensions/tutorial.html#installing-the-extension)


Configuration
-------------

::

    ckanext.ytp.drupal.connection = <Drupal database connection URL>

::

    ckanext.ytp.drupal.node_type = <Drupal node type>

::

    ckanext.ytp.drupal.translations_disabled = <Disable language support for nodes>


Connection URL is required. Node type defaults to service_alert and translations are enabled by default. 

Example configuration::

    ckanext.ytp.drupal.connection = postgresql://drupal:drupal@localhost/drupal
    ckanext.ytp.drupal.node_type = service_alert
    ckanext.ytp.drupal.translations_disabled = false
