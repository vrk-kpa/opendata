CKAN Archiver Extension
=======================

**Status:** Production

**CKAN Version:** 1.5.1+


Overview
--------
The CKAN Archiver Extension provides a set of Celery tasks for downloading
and saving CKAN resources.
It can be configured to run automatically, saving any new resources that are added
to a CKAN instance (and saving any resources when their URL is changed).
It can also be run manually from the command line in order to archive resources
for specific datasets, or to archive all resources in a CKAN instance.


Installation
------------

Install the extension as usual, e.g. (from an activated virtualenv):

::

    $ pip install -e git+http://github.com/okfn/ckanext-archiver.git#egg=ckanext-archiver

Or (primarily for developers) download the source, then from the ckanext-archiver directory run:

::

    $ pip install -e ./


Configuration
-------------

1.  Enabling Archiver
   
    If you want the archiver to run automatically when a new CKAN resource is added, or the url of a resource is changed,
    then edit your CKAN config file (eg: development.ini) to enable the extension:

    ::

        ckan.plugins = archiver

    If there are other plugins activated, add this to the list (each plugin should be separated with a space).

    **Note:** You can still run the archiver manually (from the command line) on specific resources or on all resources
    in a CKAN instance without enabling the plugin. See section 'Using Archiver' for details.

2.  Other CKAN config options

    The following config variable should also be set in your CKAN config:

    * ckan.site_url: URL to your CKAN instance

    Optionally, the following config variable can also be set:

    * ckan.cache_url_root: URL that will be prepended to the file path and saved against the CKAN resource,
      providing a full URL to the archived file.

3.  Additional Archiver settings

    The following Archiver settings can be changed by creating a copy of ``ckanext/archiver/default_settings.py``
    at ``ckanext/archiver/settings.py``, and editing the variables:

    * ARCHIVE_DIR: path to the directory that archived files will be saved to
    * MAX_CONTENT_LENGTH: the maximum size (in bytes) of files to archive
    * RETRIES: whether or not to retry on failure


Using Archiver
--------------

First, make sure that Celery is running.
For test/local use, you can do this by going to the CKAN root directory and typing:

::

    paster celeryd -c <path to CKAN config>

For production use, we recommend setting up Celery to run with supervisord.
For more information see:

* http://docs.ckan.org/en/latest/extensions.html#enabling-an-extension-with-background-tasks
* http://wiki.ckan.org/Writing_asynchronous_tasks

The Archiver can be used in two ways:

1.  Automatically

    Install, enable and configure the plugin as described above.
    Any changes to resource URLs (either adding new or updating current URLs) in the CKAN instance will 
    now call the archiver to try and download the resource.

2.  Manually

    From the ckanext-archiver directory run:

    ::

        paster archiver update [dataset] -c <path to CKAN config>

    Here ``dataset`` is an optional CKAN dataset name or ID. 
    If given, all resources for that dataset will be archived.

    If omitted, all resources for all datasets will be archived.

    For a full list of manual commands run:

    ::

        paster archiver --help


Testing
-------

Tests should be run from the CKAN root directory (not the extension root).

::

    (pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-archiver/tests/
