#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *" qa "* ]] && paster --plugin=ckanext-qa qa update -c ${APP_DIR}/production.ini
