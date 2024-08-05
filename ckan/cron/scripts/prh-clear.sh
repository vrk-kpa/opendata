#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: prh-clear"

# run commands (only run during last day of the month, if the next day is the first day of month)
[[ "$(date -d "@$(( $(date +%s) + 1 * 24 * 60 * 60 ))" +%d)" == "01" ]] && ckan -c ${APP_DIR}/production.ini prh-tools clear ${CKAN_STORAGE_PATH}/prh
