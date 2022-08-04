#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: archiver-update"

# run commands
[[ "${CKAN_PLUGINS}" == *" archiver "* ]] && ckan -c ${APP_DIR}/production.ini archiver update
