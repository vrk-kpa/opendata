#! /bin/bash -e

# CKAN Travis CI testing

SOURCE_DIRECTORY=`pwd`
VIRTUAL_ENVIRONMENT="/usr/lib/ckan/default"

. $VIRTUAL_ENVIRONMENT/bin/activate

pip install -r $VIRTUAL_ENVIRONMENT/src/ckan/dev-requirements.txt

EXIT_STATUS=0

echo "## install modules ##"
cd $SOURCE_DIRECTORY/modules
for plugin in *; do
    if [ -f $plugin/setup.py ]; then
        cp -r $plugin $VIRTUAL_ENVIRONMENT/src/
        cd $VIRTUAL_ENVIRONMENT/src/$plugin
        $VIRTUAL_ENVIRONMENT/bin/python setup.py develop
        if [ -f dev-requirements.txt ]; then
            pip install -r dev-requirements.txt
        fi
        cd $SOURCE_DIRECTORY/modules
    fi
done
cd  $SOURCE_DIRECTORY

echo "## nosetests ##"

tested_plugins=(ckanext-archiver ckanext-ytp_main ckanext-ytp_request ckanext-ytp_tasks ckanext-qa)
untested_plugins=(ckanext-datarequests ckanext-googleanalytics ckanext-harvest ckanext-spatial)

for plugin in ${tested_plugins[*]}; do
    if [ -f modules/$plugin/test.ini ]; then
        echo "Running nosetest for $plugin"
        cd $VIRTUAL_ENVIRONMENT/src/$plugin
        nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
        NOSE_EXIT=$?
        if [ "$NOSE_EXIT" != "0" ]; then
        	EXIT_STATUS=$NOSE_EXIT
        fi
        cd $SOURCE_DIRECTORY
    fi
done


deactivate

cd $SOURCE_DIRECTORY
exit $EXIT_STATUS
