#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *"ytp_main"* ]] && paster --plugin=ytp_main ytp-dataset update_package_deprecation -c ${APP_DIR}/production.ini
