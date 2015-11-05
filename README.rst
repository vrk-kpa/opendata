CKAN Quality Assurance Extension
================================

The ckanext-qa extension will check each of your dataset resources in CKAN and give
them an 'openness score' based Tim Berners-Lee's five stars of openness
(http://lab.linkeddata.deri.ie/2010/star-scheme-by-example)

It provides a report that allows you to view broken links and openness scores.

TODO: Add display the score on the dataset / resource for the default CKAN templates.


Requirements
------------

Before installing ckanext-qa, make sure that you have installed the following:

* CKAN 2.1+
* ckanext-archiver 2.0+ (http://github.com/okfn/ckanext-archiver)


Installation
------------

To install ckanext-qa, ensure you have previously installed ckanext-archiver and ckanext-report and then:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-qa Python package into your virtual environment::

     pip install -e git+http://github.com/okfn/ckanext-qa.git#egg=ckanext-qa

3. Now create the database tables::

     paster --plugin=ckanext-qa qa init --config=production.ini

4. Add ``qa`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


Upgrade from version 0.1 to 2.x
-------------------------------

NB You should upgrade ckanext-archiver and ckanext-qa from v0.1 to 2.x in one go. Upgrade them first and then carry out the following:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Upgrade the ckanext-qa Python package::

     cd ckanext-qa
     git pull
     python setup.py develop

3. Create the new database tables::

     paster --plugin=ckanext-qa qa init --config=production.ini

4. Install the developer dependencies::

     pip install -r requirements-dev.txt

5. Migrate your database to the new QA tables::

     python ckanext/qa/bin/migrate_task_status.py --write production.ini

Configuration
-------------

You must make sure that the following is set in your CKAN config:

::

    ckan.site_url = <URL to your CKAN instance>


Using The QA Extension
----------------------

**QA**: score every dataset and resource against the 5 stars of openness.

The QA runs when a dataset/resource is archived, or you can run it manually using a paster command::

    paster --plugin=ckanext-qa qa update [dataset] --config=production.ini

Here ``dataset`` is a CKAN dataset name or ID, or you can omit it to do the QA on all datasets.

For a full list of manual commands run::

    paster --plugin=ckanext-qa qa --help

Once you've done some archiving you can generate an Openness report::

    paster --plugin=ckanext-report report generate openness --config=production.ini

And view it on your CKAN site at ``/report/openness``.


Tests
-----

To run the tests:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. If not done already, install the dev requirements::

    (pyenv)~/pyenv/src/ckan$ pip install ../ckanext-qa/requirements-dev.txt

3. From the CKAN root directory (not the extension root) do::

    (pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-qa/tests/ --with-pylons=../ckanext-qa/test-core.ini
