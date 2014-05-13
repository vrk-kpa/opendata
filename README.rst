CKAN Quality Assurance Extension
================================


The ckanext-qa extension will check each of your package resources and give
these resources an openness score based Tim Berners-Lee's five stars of openness
(http://lab.linkeddata.deri.ie/2010/star-scheme-by-example)

It also provides a Dashboard that allows you to view broken links and openness scores.

Once you have run the qa commands (see 'Using The QA Extension' below),
resources and packages will have a set of openness key's stores in their
extra properties. Alter your templates to display the score for each resource/dataset.


Requirements
------------

Before installing ckanext-qa, make sure that you have installed the following:

* CKAN 1.5.1+
* ckanext-archiver (http://github.com/okfn/ckanext-archiver)


Installation
------------

Install the plugin using pip. Download it, then from the ckanext-qa directory, run

::

    $ pip install -e ./

This will register a plugin entry point, so you can now add the following
to the ``[app:main]`` section of your CKAN .ini file:

::

    ckan.plugins = qa <other-plugins>

After you reload the site, the Quality Assurance plugin
and openness score interface should be available at http://your-ckan-instance/qa


Configuration
-------------

The QA extension now depends on the CKAN Archiver extension and CKAN 1.5 (with Celery).

You must also make sure that the following is set in your CKAN config:

::

    ckan.site_url = <URL to your CKAN instance>





Using The QA Extension
----------------------

**QA**: analyze the results of the archiving step and calculating resource/package openness ratings.

This step can be performed by running the associated ``paster`` command
from the ckanext-qa directory.

::

    $ paster qa update|clean [package name/id] --config=<path to ckan config file>

``update`` or ``clean`` will either update the package resources or remove everything changed by
the QA Extension respectively.

The command can be run on just a single package by giving the package ``name`` or ``ID`` after the
``update/clean`` subcommand. If no package name is given, the database is scanned
for a list of all packages and the command is run on each one.

After you run the ``archive`` or ``qa`` commands, the QA results can be viewed
at

::

    http://your-ckan-instance/data/report


Developers
----------

You can run the test suite from the ckanext-qa directory.
The tests require nose and mock, so install them first if you have not already
done so:

::

   $ pip install nose mock

Then, run nosetests from the ckan directory

::

   $ nosetests --ckan <path to ckanext-qa>/tests --with-pylons=test-core.ini

