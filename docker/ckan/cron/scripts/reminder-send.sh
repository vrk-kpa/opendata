#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "reminder-send"

# run commands
[[ "${CKAN_PLUGINS}" == *" reminder "* ]] && paster --plugin=ckanext-reminder reminder send -c ${APP_DIR}/production.ini
