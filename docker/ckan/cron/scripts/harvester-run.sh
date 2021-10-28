#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "harvester-run"

# run commands
[[ "${CKAN_PLUGINS}" == *" harvest "* ]] && paster --plugin=ckanext-harvest harvester run -c ${APP_DIR}/production.ini
