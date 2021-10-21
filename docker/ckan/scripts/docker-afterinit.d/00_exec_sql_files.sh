#!/bin/bash
set -o pipefail

cat ${APP_DIR}/sql/00_datastore_permissions.sql | PGPASSWORD="${DB_CKAN_PASS}" psql -d ${DB_DATASTORE_READONLY} -h ${DB_HOST} -U ${DB_CKAN_USER} --set ON_ERROR_STOP=1
