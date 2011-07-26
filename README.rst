CKAN Quality Assurance Extension
================================



The ckanext-qa extension will check each of your package resources and give
these resources an openness score based Tim Berners-Lee's five stars of openness
(http://lab.linkeddata.deri.ie/2010/star-scheme-by-example)

It also provides a Dashboard that allows you to view broken links and openness scores.

Once you have run the qa commands (see 'The QA Process' below),
resources and packages will have a set of openness key's stores in their
extra properties. 
This process will also set the hash value and content_length for each 
individual resource.


Installation and Activation
---------------------------

To install the plugin, load the source:

::

    $ pip install -e hg+https://bitbucket.org/okfn/ckanext-qa#egg=ckanext-qa

This will also register a plugin entry point, so you now should be 
able to add the following to your CKAN .ini file:

::

    ckan.plugins = qa <other-plugins>

You can run the paster entry point to update or clean up package-scores
from the plugin directory using the following command:


The QA Process
--------------

The QA process is currently broken down into two main steps:

1) **Archive**: Attempt to download and save all resources.
2) **QA**: analyze the results of the archiving step and calculating resource/package
   openness ratings.

Additionally, a useful third step can be performed:

3) **Process** archived data, parsing content and making it available
   online using a REST API. This allows archived data to be easily viewed
   and manipulated by users, and in particular this is required
   if using the ckan datapreview extension.

::

    $ paster archive [update|clean] --config=../ckan/development.ini

    $ paster qa [update|clean] --config=../ckan/development.ini

    $ paster process [update|clean] --config=../ckan/development.ini
    
After you reload the site, the Quality Assurance plugin
and openness score interface should be available at http://ckan-instance/qa


API Access
----------

::
    http://ckan-instance/api/2/util/qa/


Developers
----------
You can run the test suite for ckanext-qa from the ckan directory, the tests
for ckanext-qa require nose and mock:

::

   (ckan)$ pip install nose mock
   (ckan)$ nosetests --with-pylons=test-core.ini --ckan  path/to/ckanext-qa/tests

The tests only run in PostgreSQL, hence the need to specify test-core.ini.


Deployment
----------

Create a directory for the downloads:

::

    sudo mkdir -p /var/lib/ckan/dgu/qa/download
    sudo chown www-data:ckan /var/lib/ckan/dgu/qa/download/
    sudo chmod g+w /var/lib/ckan/dgu/qa/download

Add a config option:

::

    ckan.qa_downloads = /var/lib/ckan/dgu/qa/download

Then add to the cron job:

::

    # m h  dom mon dow   command
      0 0  1   *   *     paster --plugin="ckanext-qa" package-scores update --config=/etc/ckan/dgu/dgu.ini
