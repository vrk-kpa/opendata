#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *" report "* ]] && paster --plugin=ckanext-report report generate -c ${APP_DIR}/production.ini
