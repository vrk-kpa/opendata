#!/bin/bash
set -e

# source env
. /home/ckan/.environment

echo "ytp-dataset-update-package-deprecation"

# run commands
paster --plugin=ckanext-ytp_main ytp-dataset update_package_deprecation -c ${APP_DIR}/production.ini
