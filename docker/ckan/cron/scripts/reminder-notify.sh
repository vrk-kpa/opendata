#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "reminder-notify"

# run commands
[[ "${CKAN_PLUGINS}" == *" reminder "* ]] && paster --plugin=ckanext-reminder reminder notify -c ${APP_DIR}/production.ini
