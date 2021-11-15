#!/bin/bash
set -e

echo "init_ckan() ..."

# enable nginx maintenance mode
touch /var/www/resources/.init-progress

# init filesystems
. init_filesystems.sh

# create destination dirs
mkdir -p ${APP_DIR}/sql

# apply templates and install result files
jinja2 ${APP_DIR}/templates/production.ini.j2 -o ${APP_DIR}/production.ini
jinja2 ${APP_DIR}/templates/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${APP_DIR}/templates/sql/00_datastore_permissions.sql.j2 -o ${APP_DIR}/sql/00_datastore_permissions.sql

# run prerun script that checks connections and inits db
python prerun.py || { echo '[CKAN prerun] FAILED. Exiting...' ; exit 1; }

# execute SQL scripts
cat ${APP_DIR}/sql/00_datastore_permissions.sql | PGPASSWORD="${DB_CKAN_PASS}" psql -d ${DB_DATASTORE_READONLY} -h ${DB_HOST} -U ${DB_CKAN_USER} --set ON_ERROR_STOP=1

# init ckan extensions
echo "init ckan extensions ..."
paster --plugin=ckanext-ytp_main ytp-facet-translations ${EXT_DIR}/ckanext-ytp_main/ckanext/ytp/i18n -c ${APP_DIR}/production.ini
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_platform_vocabulary -c ${APP_DIR}/production.ini
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_showcase_type_vocabulary -c ${APP_DIR}/production.ini
paster --plugin=ckan db migrate-filestore -c ${APP_DIR}/production.ini

# init ckan extension databases
echo "init ckan extension databases ..."
paster --plugin=ckanext-ytp_request initdb -c ${APP_DIR}/production.ini
paster --plugin=ckanext-harvest harvester initdb -c ${APP_DIR}/production.ini
paster --plugin=ckanext-spatial spatial initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *" archiver "* ]]     && paster --plugin=ckanext-archiver archiver init -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *" qa "* ]]           && paster --plugin=ckanext-qa qa init -c ${APP_DIR}/production.ini
paster --plugin=ckanext-report report initdb -c ${APP_DIR}/production.ini
paster --plugin=ckanext-matomo matomo init_db -c ${APP_DIR}/production.ini
paster --plugin=ckanext-cloudstorage cloudstorage initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *" rating "* ]]       && paster --plugin=ckanext-rating rating init -c ${APP_DIR}/production.ini
paster --plugin=ckanext-reminder reminder init -c ${APP_DIR}/production.ini

# rebuild solr search indexes
echo "rebuild solr search indexes ..."
paster --plugin=ckan search-index rebuild -c ${APP_DIR}/production.ini

# disable nginx maintenance mode
rm -f /var/www/resources/.init-progress