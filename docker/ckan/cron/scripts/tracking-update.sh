#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "tracking-update"

# run commands
paster --plugin=ckan tracking update -c ${APP_DIR}/production.ini
paster --plugin=ckan search-index rebuild -r -c ${APP_DIR}/production.ini
