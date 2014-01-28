#! /bin/sh -e

SOURCE_DIRECTORY=`pwd`

. /usr/lib/ckan/default/bin/activate

EXIT_STATUS=0

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
flake8 --max-line-length=120 modules/* --exclude='*.tar,ytp-tools,ckanext-drupal7'
FLAKE8_EXIT=$?

if [ "$FLAKE8_EXIT" != "0" ]; then
    EXIT_STATUS=$FLAKE8_EXIT
fi

deactivate

cd $SOURCE_DIRECTORY
exit $EXIT_STATUS
