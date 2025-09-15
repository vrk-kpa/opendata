#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: qa-update"

# run commands
[[ "${CKAN_PLUGINS}" == *" qa "* ]] && ckan -c ${APP_DIR}/ckan.ini qa update
