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

The CKAN Archiver Extension will download all of a CKAN's resources, for three purposes:

1. offer the user it as a 'cached' copy, in case the link becomes broken
2. tell the user (and publishers) if the link is broken, on both the dataset/resource and in a 'Broken Links' report
3. the downloaded file can be analysed by other extensions, such as ckanext-qa or ckanext-pacakgezip.

Demo:

.. image:: archiver_resource.png
    :alt: Broken link check info and a cached copy offered on resource

.. image:: archiver_report.png
    :alt: Broken link report

Compatibility: Requires CKAN version 2.1 or later

TODO:

* Show brokenness on the package page (not just the resources)
* Prettify the html bits
* Add brokenness to search facets using IFacet

Operation
---------

When a resource is archived, the information about the archival - if it failed, the filename on disk, file size etc - is stored in the Archival table. (In ckanext-archiver v0.1 it was stored in TaskStatus and on the Resource itself.) This is added to dataset during the package_show call (using a schema key), so the information is also available over the API.

Other extensions can subscribe to the archiver's ``IPipe`` interface to hear about datasets being archived. e.g. ckanext-qa will detect its file type and give it an openness score, or ckanext-packagezip will create a zip of the files in a dataset.

Archiver works on Celery queues, so when Archiver is notified of a dataset/resource being created or updated, it puts an 'update request' on a queue. Celery calls the Archiver 'update task' to do each archival. You can start Celery with multiple processes, to archive in parallel.

You can also trigger an archival using paster on the command-line.

By default, two queues are used:

1. 'bulk' for a regular archival of all the resources
2. 'priority' for when a user edits one-off resource

This means that the 'bulk' queue can happily run slowly, archiving large quantities slowly, such as re-archiving every single resource once a week. And meanwhile, if a new resource is put into CKAN then it can be downloaded straight away via the 'priority' queue.


Installation
------------

To install ckanext-archiver:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-archiver and ckanext-report Python packages into your virtual environment::

     pip install -e git+http://github.com/ckan/ckanext-archiver.git#egg=ckanext-archiver
     pip install -e git+http://github.com/datagovuk/ckanext-report.git#egg=ckanext-report

3. Install the archiver dependencies::

     pip install -r ckanext-archiver/requirements.txt

4. Now create the database tables::

     paster --plugin=ckanext-archiver archiver init --config=production.ini
     paster --plugin=ckanext-report report initdb --config=production.ini

4. Add ``archiver report`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

5. Install a Celery queue backend - see later section.

6. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

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

4. Also in your CKAN config file, rename old config option keys if you have them:

     * ``ckan.cache_url_root`` to ``ckanext-archiver.cache_url_root``
     * ``ckanext.archiver.user_agent_string`` to ``ckanext-archiver.user_agent_string``

5. Upgrade the ckanext-archiver Python package::

     cd ckanext-archiver
     git pull
     python setup.py develop

6. Create the new database tables::

     paster --plugin=ckanext-archiver archiver init --config=production.ini

7. Ensure the archiver dependencies are installed::

     pip install -r requirements.txt

8. Install the developer dependencies, needed for the migration::

     pip install -r dev-requirements.txt

9. Migrate your database to the new Archiver tables::

     python ckanext/archiver/bin/migrate_task_status.py --write production.ini


Installing a Celery queue backend
---------------------------------

Archiver uses Celery to manage its 'queues'. You need to install a queue back-end, such as Redis or RabbitMQ.

Redis backend
-------------

Redis can be installed like this::

    sudo apt-get install redis-server

Install the python library into your python environment::

    /usr/lib/ckan/default/bin/activate/pip install redis==2.10.1

It must then be configured in your CKAN config (e.g. production.ini) by inserting a new section, e.g. before `[app:main]`::

    [app:celery]
    BROKER_BACKEND = redis
    BROKER_HOST = redis://localhost/1
    CELERY_RESULT_BACKEND = redis
    REDIS_HOST = 127.0.0.1
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_CONNECT_RETRY = True

Number of items in the queue 'bulk'::

    redis-cli -n 1 LLEN bulk

See item 0 in the queue (which is the last to go on the queue & last to be processed)::

    redis-cli -n 1 LINDEX bulk 0

To delete all the items on the queue::

    redis-cli -n 1 DEL bulk

Installing SNI support
----------------------

When archiving resources on servers which use HTTPS, you might encounter this error::

    requests.exceptions.SSLError: [Errno 1] _ssl.c:504: error:14077410:SSL routines:SSL23_GET_SERVER_HELLO:sslv3 alert handshake failure

Whilst this could possibly be a problem with the server, it is most likely due to you needing to install SNI support on the machine that ckanext-archiver runs. Server Name Indication (SNI) is for when a server has multiple SSL certificates, which is a relatively new feature in HTTPS. This requires installing a recent version of OpenSSL plus the python libraries to make use of this feature.

If you have SNI support installed then this should command run without the above error::

    python -c 'import requests; requests.get("http://files.datapress.com")'

On Ubuntu 12.04 you can install SNI support by doing this::

    sudo apt-get install libffi-dev
    . /usr/lib/ckan/default/bin/activate
    pip install 'cryptography==0.9.3' pyOpenSSL ndg-httpsclient pyasn1

You should also check your OpenSSL version is greater than 1.0.0::

    python -c "import ssl; print ssl.OPENSSL_VERSION"

Apparently SNI was added into OpenSSL version 0.9.8j but apparently there are reported problems with 0.9.8y, 0.9.8zc & 0.9.8zg so 1.0.0+ is recommended.

For more about enabling SNI in python requests see:

    * https://stackoverflow.com/questions/18578439/using-requests-with-tls-doesnt-give-sni-support/18579484#18579484
    * https://github.com/kennethreitz/requests/issues/2022


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

    * ``ckan.site_url`` = URL to your CKAN instance

    This is the URL that the archive process (in Celery) will use to access the CKAN API to update it about the cached URLs. If your internal network names your CKAN server differently, then specify this internal name in config option: ``ckan.site_url_internally``


3.  Additional Archiver settings

    Add the settings to the CKAN config file:

      * ``ckanext-archiver.archive_dir`` = path to the directory that archived files will be saved to (e.g. ``/www/resource_cache``)
      * ``ckanext-archiver.cache_url_root`` = URL where you will be publicly serving the cached files stored locally at ckanext-archiver.archive_dir.
      * ``ckanext-archiver.max_content_length`` = the maximum size (in bytes) of files to archive (default ``50000000`` =50MB)
      * ``ckanext-archiver.user_agent_string`` = identifies the archiver to servers it archives from

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

    paster --plugin=ckanext-archiver celeryd2 run all -c development.ini

However in production you'd run the priority and bulk queues separately, or else the priority queue will not have any priority over the bulk queue. This can be done by running these two commands in separate terminals::

    paster --plugin=ckanext-archiver celeryd2 run priority -c production.ini
    paster --plugin=ckanext-archiver celeryd2 run bulk -c production.ini

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

    (pyenv)~/pyenv/src/ckan$ pip install ../ckanext-archiver/dev-requirements.txt

3. From the CKAN root directory (not the extension root) do::

    (pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-archiver/tests/ --with-pylons=../ckanext-archiver/test-core.ini


Questions
---------

The archiver information is not appearing on the resource page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check that it is appearing in the API for the dataset - see question below.

The archiver information is not appearing in the API (package_show)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

i.e. if you browse this path on your website: `/api/action/package_show?id=<package_name>` then you don't see the `archiver` key at the dataset level or resource level.

Check the `paster archiver update` command completed ok. Check that the `paster celeryd2 run` has done the archiving ok. Check the dataset has at least one resource. Check that you have ``archiver`` in your ckan.plugins and have restarted CKAN.

'SSL handshake' error
~~~~~~~~~~~~~~~~~~~~~

When archiving resources on servers which use HTTPS, you might encounter this error::

    requests.exceptions.SSLError: [Errno 1] _ssl.c:504: error:14077410:SSL routines:SSL23_GET_SERVER_HELLO:sslv3 alert handshake failure

This is probably because you don't have SNI support and requires installing OpenSSL - see section "Installing SNI support".
