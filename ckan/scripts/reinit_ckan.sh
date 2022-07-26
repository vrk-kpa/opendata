#!/bin/bash
set -e

echo "reinit_ckan ..."

# apply templates
jinja2 ${TEMPLATE_DIR}/production.ini.j2 -o ${APP_DIR}/production.ini
jinja2 ${TEMPLATE_DIR}/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${TEMPLATE_DIR}/datastore_permissions.sql.j2 -o ${SCRIPT_DIR}/datastore_permissions.sql

# run prerun script that checks connections and inits db
python prerun.py || { echo '[CKAN prerun] FAILED. Exiting...' ; exit 1; }

echo "Upgrade CKAN database ..."
ckan -c ${APP_DIR}/production.ini db upgrade