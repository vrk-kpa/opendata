#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${MATOMO_ENABLED}" == "true" ]] && paster --plugin=ckanext-matomo matomo fetch -c ${APP_DIR}/production.ini
