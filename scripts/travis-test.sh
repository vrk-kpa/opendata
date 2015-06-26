#! /bin/sh -e

# CKAN Travis CI testing

SOURCE_DIRECTORY=`pwd`
VIRTUAL_ENVIRONMENT="/usr/lib/ckan/default"

. $VIRTUAL_ENVIRONMENT/bin/activate

EXIT_STATUS=0

echo "## install modules ##"
for plugin in modules/*; do
    if [ -f $plugin/setup.py ]; then
        cd $plugin
        sudo $VIRTUAL_ENVIRONMENT/bin/python setup.py develop
        cd $SOURCE_DIRECTORY
    fi
done


echo "## nosetests ##"

for plugin in modules/*; do
    if [ -f $plugin/test.ini ]; then
        echo "Running nosetest for $plugin"
        cd $plugin
        nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
        NOSE_EXIT=$?
        if [ "$NOSE_EXIT" != "0" ]; then
        	EXIT_STATUS=$NOSE_EXIT
        fi
        cd $SOURCE_DIRECTORY
    fi
done

echo "## flake8 ##"
flake8 --max-line-length=160 modules/* --exclude='*.tar,ckanext-drupal7,ckanext-googleanalytics'
FLAKE8_EXIT=$?

if [ "$FLAKE8_EXIT" != "0" ]; then
    EXIT_STATUS=$FLAKE8_EXIT
fi

deactivate

cd $SOURCE_DIRECTORY
exit $EXIT_STATUS
