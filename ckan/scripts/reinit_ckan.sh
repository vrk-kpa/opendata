#!/bin/bash
set -e

echo "reinit_ckan ..."

# apply templates
jinja2 ${TEMPLATE_DIR}/ckan.ini.j2 -o ${APP_DIR}/ckan.ini
jinja2 ${TEMPLATE_DIR}/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${TEMPLATE_DIR}/ckan-uwsgi.ini.j2 -o ${APP_DIR}/ckan-uwsgi.ini
jinja2 ${TEMPLATE_DIR}/datastore_permissions.sql.j2 -o ${SCRIPT_DIR}/datastore_permissions.sql

# run prerun script that checks connections and inits db
python connection_check.py || { echo '[CKAN connection check] FAILED. Exiting...' ; exit 1; }

echo "Init CKAN database ..."
ckan -c ${APP_DIR}/ckan.ini db init

echo "Upgrade CKAN database ..."
ckan -c ${APP_DIR}/ckan.ini db upgrade
ckan -c ${APP_DIR}/ckan.ini db upgrade -p apis
ckan -c ${APP_DIR}/ckan.ini db upgrade -p harvest
