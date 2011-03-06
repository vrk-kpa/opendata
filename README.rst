Quality Assurance Extension
===========================

The QA plugin crawls resources and scores them for openness. It also provides
a Dashboard that allows you to view broken links and openness scores.

Installation and Activation
---------------------------

To install the plugin, enter your virtualenv and load the source:

::

    (ckan)$ pip install -e hg+https://bitbucket.org/okfn/ckanext-qa#egg=ckanext-qa

This will also register a plugin entry point, so you now should be 
able to add the following to your CKAN .ini file:

::

    ckan.plugins = qa <other-plugins>

You can run the paster entry point to update or clean up package-scores
from the plugin directory using the following command:

::

    (ckan)$ paster package-scores [update|clean] --config=../ckan/development.ini
    
After you clear your cache and reload the site, the Quality Assurance plugin
and openness score interface should be available at http://myckaninstance/qa

About QA Extension
------------------

The ckanext-qa extension will check each of your package resources and give
these resources an openness score based timbl's five stars of openness.

Once you have run the package-scores command with the update option, your
resources and packages will have a set of openness key's stores in their
extra properties. This process will also set the hash value and content_length
for each individual resource.

Developers
----------
You can run the test suite for ckanext-qa from the ckan directory, the tests
for ckanext-qa require nose and mock:

::

   (ckan)$ pip install nose mock
   (ckan)$ nosetests -x path/to/ckanext-qa/tests --ckan

You will need to edit your ``test.ini`` file to use PostgreSQL. The tests do
not run on SQLite. You can do that by commenting out the two SQLite override
options in ``test.ini`` so that the PostgreSQL config options in
``test-core.ini`` are used instead.

::

    #faster_db_test_hacks = True
    #sqlalchemy.url = sqlite:///


