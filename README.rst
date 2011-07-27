CKAN Quality Assurance Extension
================================



The ckanext-qa extension will check each of your package resources and give
these resources an openness score based Tim Berners-Lee's five stars of openness
(http://lab.linkeddata.deri.ie/2010/star-scheme-by-example)

It also provides a Dashboard that allows you to view broken links and openness scores.

Once you have run the qa commands (see 'Using The QA Extension' below),
resources and packages will have a set of openness key's stores in their
extra properties. 
This process will also set the hash value and content_length for each 
individual resource.


Installation
------------

Install the plugin using pip. You can either download it, then
from the ckanext-qa directory, run

::

    $ pip install -e ./

Or, you can install it directly from the OKFN bitbucket repository:

::

    $ pip install -e hg+https://bitbucket.org/okfn/ckanext-qa#egg=ckanext-qa

This will register a plugin entry point, so you can now add the following 
to the ``[app:main]`` section of your CKAN .ini file:

::

    ckan.plugins = qa <other-plugins>

After you reload the site, the Quality Assurance plugin
and openness score interface should be available at http://your-ckan-instance/qa


Configuration
-------------

Create a directory for the downloads:

::

    sudo mkdir -p /var/lib/ckan/dgu/qa/download
    sudo chown www-data:ckan /var/lib/ckan/dgu/qa/download/
    sudo chmod g+w /var/lib/ckan/dgu/qa/download

Add this a config option containing the path to this directory to your CKAN .ini file:

::

    ckan.qa_archive = /var/lib/ckan/dgu/qa/download

If you plan to use a local webstore to make processed resources available online,
then you must also set the webstore url in the CKAN .ini file.

(eg: if using the datapreview plugin. See the sections 'Using The QA Extension'
and 'Webstore Integration' for more information).

::

    ckan.webstore_url = http://test-webstore.ckan.net

You can create cron jobs for each of the QA commands:

::

    # m h  dom mon dow   command
      0 0  1   *   *     paster --plugin="ckanext-qa" archive update --config=/etc/ckan/dgu/dgu.ini
      0 0  1   *   *     paster --plugin="ckanext-qa" qa update --config=/etc/ckan/dgu/dgu.ini
      0 0  1   *   *     paster --plugin="ckanext-qa" process update --config=/etc/ckan/dgu/dgu.ini


Using The QA Extension
----------------------

The QA process is currently broken down into two main steps:

* **Archive**: Attempt to download and save all resources.
* **QA**: analyze the results of the archiving step and calculating resource/package
   openness ratings.

Additionally, a useful third step can be performed:

* **Process** archived data, parsing content and making it available
   online using a REST API. This allows archived data to be easily viewed
   and manipulated by users, and in particular this is required
   if using the ckan datapreview extension.

Each of these three steps can be performed by running the associated ``paster`` command
from the ckanext-qa directory.

::

    $ paster archive update|clean [package name/id] [--limit=N] --config=../ckan/development.ini

    $ paster qa update|clean [package name/id] [--limit=N] --config=../ckan/development.ini

    $ paster process update|clean [package name/id] --config=../ckan/development.ini
    
For each command you must specify either ``update`` or ``clean`` as subcommand, which will either
download/update/process the package resources or remove everything changed by the QA Extension
respectively.

Each command can be run on just a single package by giving the package ``name`` or ``ID`` after the
``update/clean`` subcommand. If no package name is given, the database is scanned
for a list of all packages and the command is run on each one.

An additional ``limit`` parameter can specified for the ``archive`` and ``qa`` commands, which
will stop the command after it has processed ``N`` packages.

After you run the ``archive`` and ``qa`` commands, the QA results can be viewed
at 

::

    http://your-ckan-instance/qa


Webstore Integration
--------------------

**Webstore Overview**

The webstore is a RESTful data store for tabular and table-like data. 
It can be used as a dynamic storage for table data, allowing filtered, 
partial or full retrieval and format conversion.
For more information see http://github.com/okfn/webstore


**Use With QA**

By using the webstore, it is possible to make archived resources accessible
using a RESTful API. This is done by using the ``process`` paster command.
When ``process`` is run, it goes through each resource that has been downloaded
and attempts to parse it and put it in the webstore database.
This data can then be used by other applications, such as the ckanext-datapreview extension.

**Configuring A Webstore For Use With The QA Extension**

It is recommended that you use the same directory for the webstore that you
use for QA archiving.  To do this, make sure that the ``SQLITE_DIR`` config 
value in the webstore application is set to the same value as the 
``ckan.qa_archive`` config value. For example, you could hardcode this value into 
the webstore configuration options, or add the following to the webstore WSGI file:

::

    from webstore.web import app as application
    application.config['SQLITE_DIR'] = '/path/to/qa_archive'

It is possible to use other directories but this would
currently require reconfiguring paths in the ``commands/process.py`` file
and making sure that the web server has read/write access to the directories.


API Access
----------

The QA Extension exposes the following API endpoints:

::

    http://your-ckan-instance/api/2/util/qa/


Developers
----------

You can run the test suite from the ckanext-qa directory.
The tests require nose and mock, so install them first if you have not already
done so:

::

   $ pip install nose mock

Then, run nosetests from the ckanext-qa directory

::

   $ nosetests --ckan
