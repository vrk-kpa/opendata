#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "start-prh-crawler"

# run commands
paster --plugin=ckanext-prh prh-tools fetch-data ${CKAN_STORAGE_PATH}/prh --package_id=yritykset -c ${APP_DIR}/production.ini
