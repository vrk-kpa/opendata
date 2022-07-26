#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: report-generate"

# run commands
[[ "${CKAN_PLUGINS}" == *" report "* ]] && ckan -c ${APP_DIR}/production.ini report generate
