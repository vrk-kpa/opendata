Quality Assurance Extension
===========================

The QA plugin crawls resources and scores them for openness. It also provides
a Dashboard that allows you to view broken links and openness scores.

Installation and Activation
---------------------------

To install the plugin, enter your virtualenv and load the source::

 (ckan)$ pip install -e hg+https://bitbucket.org/okfn/ckanext-qa#egg=ckanext-qa

This will also register a plugin entry point, so you now should be 
able to add the following to your CKAN .ini file::

 ckan.plugins = qa <other-plugins>
  
After you clear your cache and reload the site, the Quality Assurance plugin
and openness score interface should be available at http://myckaninstance/qa

You can run the test suite for ckanext-qa:

 (ckan)$ nosetests -x tests/ --ckan --with-pylons=path/to/your/test.ini

You can run the paster entry point to update or clean up package-scores
using the following command::

 (ckan)$ paster package-scores [update|clean]

