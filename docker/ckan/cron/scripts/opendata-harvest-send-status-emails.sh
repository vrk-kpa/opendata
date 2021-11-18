#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "opendata-harvest-send-status-emails"

# run commands
paster --plugin=ckanext-ytp_main opendata-harvest send-status-emails -c ${APP_DIR}/production.ini
