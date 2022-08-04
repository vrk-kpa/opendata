#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: harvest-stuck-reports"

# run commands
ckan -c ${APP_DIR}/production.ini opendata-harvest send-stuck-runs-report
