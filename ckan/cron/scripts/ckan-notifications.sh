#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: ckan-notifications"

# run commands
ckan -c ${APP_DIR}/production.ini post /api/action/send_email_notifications > /dev/null
