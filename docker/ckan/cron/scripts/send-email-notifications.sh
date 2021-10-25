#!/bin/bash
set -e

# source env
. /home/ckan/.environment

# run commands
paster --plugin=ckan post -c ${APP_DIR}/production.ini /api/action/send_email_notifications > /dev/null
