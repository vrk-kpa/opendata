.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/datagovuk/ckanext-archiver.svg?branch=master
    :target: https://travis-ci.org/datagovuk/ckanext-archiver

=============
ckanext-archiver
=============

Overview
--------

The CKAN Archiver Extension will download CKAN resources, which can be offered to the user as a 'cached' copy. In addition it provides a 'Broken Links' report showing which resource URLs don't work.

TODO:
* Link to the cached file from the dataset
* Link to the reports (including Broken Links) from the main nav
* Mark brokenness on the dataset & resource

When a resource is archived, the information about the archival - if it failed, the filename on disk, file size etc - is stored in the Archival table. (In ckanext-archiver v0.1 it was stored in TaskStatus and on the Resource itself.)

Other extensions can subscribe to the archiver's ``IPipe`` interface to hear about datasets being archived. e.g. ckanext-qa will detect its file type and give it an openness score, or ckanext-packagezip will create a zip of the files in a dataset.

Archiver works on Celery queues, so when Archiver is notified of a dataset/resource being created or updated, it puts an 'update request' on a queue. Celery calls the Archiver 'update task' to do each archival. You can start Celery with multiple processes, to archive in parallel.

You can also trigger an archival using paster on the command-line.

By default, two queues are used:

1. 'bulk' for a regular archival of all the resources
2. 'priority' for when a user edits one-off resource

This means that the 'bulk' queue can happily run slowly, archiving large quantities slowly, such as re-archiving every single resource once a week. And meanwhile, if a new resource is put into CKAN then it can be downloaded straight away via the 'priority' queue.

Compatibility: Requires CKAN version 2.1 or later (but can be easily adapted for older versions).

Installation
------------

To install ckanext-archiver:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-archiver and ckanext-report Python packages into your virtual environment::

     pip install -e git+http://github.com/okfn/ckanext-archiver.git#egg=ckanext-archiver
     pip install -e git+http://github.com/datagovuk/ckanext-report.git#egg=ckanext-report

3. Now create the database tables::

     paster --plugin=ckanext-archiver archiver init --config=production.ini
     paster --plugin=ckanext-report report initdb --config=production.ini

4. Add ``archiver report`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

Upgrade from version 0.1 to 2.x
-------------------------------

NB If upgrading ckanext-archiver and use ckanext-qa too, then you will need to upgrade ckanext-qa to version 2.x at the same time.

NB Previously you needed both ckanext-archiver and ckanext-qa to see the broken link report. This functionality has now moved to ckanext-archiver. So now you only need ckanext-qa if you want the 5 stars of openness functionality.

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install ckanext-report (if not already installed)

     pip install -e git+http://github.com/datagovuk/ckanext-report.git#egg=ckanext-report

3. Add ``report`` to the ``ckan.plugins`` setting in your CKAN config file (it
   should already have ``archiver``) (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Upgrade the ckanext-archiver Python package::

     cd ckanext-archiver
     git pull
     python setup.py develop

5. Create the new database tables::

     paster --plugin=ckanext-archiver archiver init --config=production.ini

6. Install the developer dependencies::

     pip install -r requirements-dev.txt

7. Migrate your database to the new Archiver tables::

     python ckanext/archiver/bin/migrate_task_status.py --write production.ini

Config settings
---------------

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

    Add the settings to the CKAN config file:

      * ckanext-archiver.archive_dir - path to the directory that archived files will be saved to (e.g. ``/www/resource_cache``)
      * ckanext-archiver.max_content_length - the maximum size (in bytes) of files to archive (default ``50000000`` =50MB)

4.  Nightly report generation

    Configure the reports to be generated each night using cron. e.g.::

        0 6  * * *  www-data  /usr/lib/ckan/default/bin/paster --plugin=ckanext-report report generate --config=/etc/ckan/default/production.ini

5.  Your web server should serve the files from the archive_dir.

    With nginx you insert a new ``location`` after the ckan one. e.g. here we have configured ``ckanext-archiver.archive_dir`` to ``/www/resource_cache`` and serve these files at location ``/resource_cache`` (i.e. ``http://mysite.com/resource_cache`` )::

        server {
            # ckan
            location / {
                proxy_pass http://127.0.0.1:8080/;
                ...
            }
            # archived files
            location /resource_cache {
                root /www/resource_cache;
            }

Legacy settings:

   Older versions of ckanext-archiver put these settings in
   ckanext/archiver/settings.py as variables ARCHIVE_DIR and MAX_CONTENT_LENGTH
   but this is deprecated as of ckanext-archiver 2.0.

   There used to be an option DATA_FORMATS for filtering the resources
   archived, but that has now been removed in ckanext-archiver v2.0, since it
   is now not only caching files, but is seen as a broken link checker, which
   applies whatever the format.


Using Archiver
--------------

First, make sure that Celery is running for each queue. For test/local use, you can run::

    paster --plugin=ckan celeryd --queue=priority -c production.ini

and in a separate terminal::

    paster --plugin=ckan celeryd --queue=bulk -c production.ini

For production use, we recommend setting up Celery to run with supervisord.
For more information see:

* http://docs.ckan.org/en/latest/extensions.html#enabling-an-extension-with-background-tasks
* http://wiki.ckan.org/Writing_asynchronous_tasks

An archival can be triggered by adding a dataset with a resource or updating a resource URL. Alternatively you can run::

    paster --plugin=ckanext-archiver archiver update [dataset] --queue=priority -c <path to CKAN config>

Here ``dataset`` is a CKAN dataset name or ID, or you can omit it to archive all datasets.

For a full list of manual commands run::

    paster --plugin=ckanext-archiver archiver --help

Once you've done some archiving you can generate a Broken Links report::

    paster --plugin=ckanext-report report generate broken-links --config=production.ini

And view it on your CKAN site at ``/report/broken-links``.


Testing
-------

To run the tests:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. If not done already, install the dev requirements::

    (pyenv)~/pyenv/src/ckan$ pip install ../ckanext-archiver/requirements-dev.txt

3. From the CKAN root directory (not the extension root) do::

    (pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-archiver/tests/ --with-pylons=../ckanext-archiver/test-core.ini
