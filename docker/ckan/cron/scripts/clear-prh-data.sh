#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "clear-prh-data"

# run commands (only run during last day of the month)
[[ "$(date --date=tomorrow +\%d)" == "01" ]] && paster --plugin=ckanext-prh prh-tools clear ${CKAN_STORAGE_PATH}/prh -c ${APP_DIR}/production.ini
