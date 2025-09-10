#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: dataset-deprecations"

# run commands
ckan -c ${APP_DIR}/ckan.ini opendata-dataset update_package_deprecation
