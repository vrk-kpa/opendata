#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: reminder-notify"

# run commands
[[ "${CKAN_PLUGINS}" == *" reminder "* ]] && ckan -c ${APP_DIR}/ckan.ini reminder notify
