#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *" archiver "* ]] && paster --plugin=ckanext-archiver archiver update -c ${APP_DIR}/production.ini
