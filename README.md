Quality Assurance Extension
===========================

The QA plugin crawls resources and scores them for openness. It also provides
a Dashboard that allows you to view broken links and openness scores.

Installation and Activation
---------------------------

To install the plugin, enter your virtualenv and load the source::

 (ckan)$ pip install -e hg+https://bitbucket.org/okfn/ckanext-qa#egg=ckanext-qa

You can run the test suite for ckanext-qa:

 (ckan)$ python setup.py test

This will also register a plugin entry point, so you now should be 
able to add the following to your CKAN .ini file::

 ckan.plugins = qa <other-plugins>
 
After clearing your cache and reloading the web server, comments 
should now be available on package pages and on the home page.
