#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "archiver-notifications"

# run commands
[[ "${CKAN_PLUGINS}" == *" archiver "* ]] && paster --plugin=ckanext-archiver archiver send_broken_link_notification -c ${APP_DIR}/production.ini
