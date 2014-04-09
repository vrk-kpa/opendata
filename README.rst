CKAN Archiver Extension
=======================

**Status:** Production

**CKAN Version:** release-1.7.1-dgu


Overview
--------
The CKAN Archiver Extension will download CKAN resources. It runs as a Celery
process, and takes instructions from a queue to download each resource. These
instructions can come from:
1. CKAN every time a resources that are added
2. the command line
Many Archiver processes can be started to run in parallel, all using the same
queue.

By default, two queues are used:
1. 'bulk' for a regular archival of all the resources
2. 'priority' for when a user edits one-off resource

This means that the 'bulk' queue can happily run slowly, chugging through the downloads, say once a week. And meanwhile, if a new resource is put into CKAN then it can be downloaded straight away on the 'priority' queue.

Installation
------------

Install the extension source as usual, e.g. (from an activated virtualenv)::

    $ pip install -e git+http://github.com/datagovuk/ckanext-archiver.git#egg=ckanext-archiver

Or (primarily for developers) download the source, then from the ckanext-archiver directory run::

    $ pip install -e ./

Whichever way you install the source, you now must create the database tables::

    $ paster --plugin=ckanext-archiver archiver init --config=ckan.ini


Configuration
-------------

1.  Enabling Archiver to listen to resource changes
   
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

    This is the URL that the archive process (in Celery) will use to access the CKAN API to update it about the cached URLs. If your internal network names your CKAN server differently, then specify this internal name in config option: ckan.site_url_internally

    * ckan.cache_url_root: URL that will be prepended to the file path and saved against the CKAN resource,
      providing a full URL to the archived file.

3.  Additional Archiver settings

    The following Archiver settings can be changed by creating a copy of ``ckanext/archiver/default_settings.py``
    at ``ckanext/archiver/settings.py``, and editing the variables:

    * ARCHIVE_DIR: path to the directory that archived files will be saved to
    * MAX_CONTENT_LENGTH: the maximum size (in bytes) of files to archive

   Alternatively, if you are running CKAN with this patch: 
   https://github.com/datagovuk/ckan/commit/83dcaf3d875d622ee0cd7f3c1f65ec27a970cd10
   then you can instead add the settings to the CKAN config file as normal:

    * ckanext-archiver.archive_dir
    * ckanext-archiver.max_content_length


Using Archiver
--------------

First, make sure that Celery is running for each queue
For test/local use, you can do this by going to the CKAN root directory and typing::

    paster celeryd --queue=priority -c <path to CKAN config>

and in a separate terminal::

    paster celeryd --queue=bulk -c <path to CKAN config>

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

        paster archiver update [dataset] --queue=priority -c <path to CKAN config>

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

    (pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-archiver/tests/ --with-pylons=../ckanext-archiver/test.ini
