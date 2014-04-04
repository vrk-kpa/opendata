CKAN Drupal7 Authentication
===========================

This extension allows Drupal7 accounts to be used with CKAN.  The Drupal7
authentication replaces that of CKAN and the normal CKAN registering,
editing and logging in is replaced by Drupal7's.


Configuration
-------------

You must also make sure that the following are set in your CKAN config:

::

    ckanext.drupal7.domain = <The domain that Drupal is on>

::

    ckanext.drupal7.sysadmin_role = <Drupal role that makes users sysadmins>

::

    ckanext.drupal7.connection = <database connection string>


Example configuration::

    ckanext.drupal7.domain = localhost
    ckanext.drupal7.sysadmin_role = ckan admin
    ckanext.drupal7.connection = postgresql://drupal:pass@localhost/drupal


