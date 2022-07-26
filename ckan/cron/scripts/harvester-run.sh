#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: harvester-run"

# run commands
[[ "${CKAN_PLUGINS}" == *" harvest "* ]] && ckan -c ${APP_DIR}/production.ini harvester run
