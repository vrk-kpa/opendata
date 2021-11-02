#!/bin/bash
set -e

echo "reinit_ckan() ..."

# create destination dirs
mkdir -p ${APP_DIR}/sql

# apply templates and install result files
jinja2 ${APP_DIR}/templates/production.ini.j2 -o ${APP_DIR}/production.ini
jinja2 ${APP_DIR}/templates/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${APP_DIR}/templates/sql/00_datastore_permissions.sql.j2 -o ${APP_DIR}/sql/00_datastore_permissions.sql

# run prerun script that checks connections and inits db
python prerun.py || { echo '[CKAN prerun] FAILED. Exiting...' ; exit 1; }
