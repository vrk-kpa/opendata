#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: prh-start"

# run commands
ckan -c ${APP_DIR}/production.ini prh-tools fetch-data ${CKAN_STORAGE_PATH}/prh --package_id=yritykset
