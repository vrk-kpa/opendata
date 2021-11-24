#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "opendata-harvest-send-stuck-runs-report"

# run commands
paster --plugin=ckanext-ytp_main opendata-harvest send-stuck-runs-report -c ${APP_DIR}/production.ini
