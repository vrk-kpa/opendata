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

(eg: if using the datapreview plugin. See the section 'Using The QA Extension'
for more information).

::

    ckan.webstore_url = http://127.0.0.1:8080

You can create cron jobs for each of the QA commands:

::

    # m h  dom mon dow   command
      0 0  1   *   *     paster --plugin="ckanext-qa" archive update --config=/etc/ckan/dgu/dgu.ini
      0 0  1   *   *     paster --plugin="ckanext-qa" qa update --config=/etc/ckan/dgu/dgu.ini
      0 0  1   *   *     paster --plugin="ckanext-qa" process update --config=/etc/ckan/dgu/dgu.ini


Using The QA Extension
----------------------

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
and openness score interface should be available at http://your-ckan-instance/qa


API Access
----------

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
