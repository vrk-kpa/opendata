#! /bin/sh

PLUGINS="ckanext-ytp-groups ckanext-ytp-theme ckanext-ytp-drupal"

SOURCE_DIRECTORY=`pwd`

. /usr/lib/ckan/default/bin/activate

EXIT_STATUS=0

echo "## nosetests ##"

cd /usr/lib/ckan/default/src/
for plugin in $PLUGINS; do
    if [ -f $plugin/test.ini ]; then
        echo "Running nosetest for $plugin"
        cd $plugin
        nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
        NOSE_EXIT=$?
        if [ "$NOSE_EXIT" != "0" ]; then
        	EXIT_STATUS=$NOSE_EXIT
        fi
        cd /usr/lib/ckan/default/src/
    fi
done

#cd $SOURCE_DIRECTORY
cd /usr/lib/ckan/default/src/
echo "## flake8 ##"
flake8 --max-line-length=120 $PLUGINS
FLAKE8_EXIT=$?

if [ "$FLAKE8_EXIT" != "0" ]; then
    EXIT_STATUS=$FLAKE8_EXIT
fi

deactivate
exit $EXIT_STATUS

