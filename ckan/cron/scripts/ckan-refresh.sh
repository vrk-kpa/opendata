#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: ckan-refresh"

# run commands
ckan -c ${APP_DIR}/ckan.ini tracking update
ckan -c ${APP_DIR}/ckan.ini search-index rebuild -r
