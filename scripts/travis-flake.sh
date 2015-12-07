#! /bin/bash -e

# CKAN Travis CI flake testing

SOURCE_DIRECTORY=`pwd`




echo "## flake8 ##"
flake8 --max-line-length=160 modules/* --exclude='*.tar,ckanext-drupal7,ckanext-googleanalytics,ckanext-archiver,ckanext-qa,ckanext-harvest,ckanext-spatial,ckanext-datarequests,ckanext-report,ckanext-dcat'
FLAKE8_EXIT=$?




exit $FLAKE8_EXIT