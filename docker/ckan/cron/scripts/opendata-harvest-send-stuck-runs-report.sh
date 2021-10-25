#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
[[ "${CKAN_PLUGINS}" == *"ytp_main"* ]] && paster --plugin=ytp_main opendata-harvest send-stuck-runs-report -c ${APP_DIR}/production.ini
