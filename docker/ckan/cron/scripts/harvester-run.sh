#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *" harvest "* ]] && paster --plugin=ckanext-harvest harvester run -c ${APP_DIR}/production.ini
