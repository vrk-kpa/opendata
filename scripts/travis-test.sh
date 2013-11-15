#! /bin/sh

PLUGINS_ROOT="ckan/plugins"
SOURCE_DIRECTORY=`pwd`

. /usr/lib/ckan/default/bin/activate

EXIT_STATUS=0

echo "## nosetests ##"

for plugin in $PLUGINS_ROOT/*; do
	cd $plugin
	python setup.py develop
	nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
	NOSE_EXIT=$?
	if [ "$NOSE_EXIT" != "0" ]; then
		EXIT_STATUS=$NOSE_EXIT
	fi
	cd -
done
deactivate

cd $SOURCE_DIRECTORY

echo "## flake8 ##"
flake8 --max-line-length=120 $PLUGINS_ROOT
FLAKE8_EXIT=$?

if [ "$FLAKE8_EXIT" != "0" ]; then
    EXIT_STATUS=$FLAKE8_EXIT
fi

exit $EXIT_STATUS
