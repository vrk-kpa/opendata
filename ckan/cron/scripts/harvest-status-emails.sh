#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: harvest-status-emails"

# run commands
ckan -c ${APP_DIR}/ckan.ini opendata-harvest send-status-emails
