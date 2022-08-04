#!/bin/bash
set -e

echo "init_ckan ..."

# synchronize persistent data files
rsync -au ${DATA_DIR}_base/. ${DATA_DIR}

# apply templates
jinja2 ${TEMPLATE_DIR}/production.ini.j2 -o ${APP_DIR}/production.ini
jinja2 ${TEMPLATE_DIR}/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${TEMPLATE_DIR}/datastore_permissions.sql.j2 -o ${SCRIPT_DIR}/datastore_permissions.sql

# run prerun script that checks connections and inits db
python prerun.py || { echo '[CKAN prerun] FAILED. Exiting...' ; exit 1; }

echo "Upgrade CKAN database ..."
ckan -c ${APP_DIR}/production.ini db upgrade

# minify JS files
ckan -c ${APP_DIR}/production.ini minify ${SRC_DIR}/ckan/public/base/javascript

# execute SQL scripts
cat ${SCRIPT_DIR}/datastore_permissions.sql | PGPASSWORD="${DB_CKAN_PASS}" psql -d ${DB_DATASTORE_READONLY} -h ${DB_HOST} -U ${DB_CKAN_USER} --set ON_ERROR_STOP=1

# init ckan extensions
echo "init ckan extensions ..."
#ckan -c ${APP_DIR}/production.ini opendata add-facet-translations ${EXT_DIR}/ckanext-ytp_main/ckanext/ytp/i18n
ckan -c ${APP_DIR}/production.ini sixodp-showcase create_platform_vocabulary
ckan -c ${APP_DIR}/production.ini sixodp-showcase create_showcase_type_vocabulary

# init ckan extension databases
echo "init ckan extension databases ..."
ckan -c ${APP_DIR}/production.ini opendata-model initdb
ckan -c ${APP_DIR}/production.ini opendata-request init-db
ckan -c ${APP_DIR}/production.ini harvester initdb
ckan -c ${APP_DIR}/production.ini spatial initdb
[[ "${CKAN_PLUGINS}" == *" archiver "* ]]     && ckan -c ${APP_DIR}/production.ini archiver init
[[ "${CKAN_PLUGINS}" == *" qa "* ]]           && ckan -c ${APP_DIR}/production.ini qa init
ckan -c ${APP_DIR}/production.ini report initdb
[[ "${MATOMO_ENABLED}" == "true" ]]           && ckan -c ${APP_DIR}/production.ini matomo init_db
[[ "${CKAN_CLOUDSTORAGE_ENABLED}" == "true" ]]           && ckan -c ${APP_DIR}/production.ini cloudstorage initdb
[[ "${CKAN_PLUGINS}" == *" rating "* ]]       && ckan -c ${APP_DIR}/production.ini rating init
ckan -c ${APP_DIR}/production.ini reminder initdb
ckan -c ${APP_DIR}/production.ini recommendations init

# Import municipality data
ckan -c ${APP_DIR}/production.ini opendata-model populate-municipality-bounding-box

# refresh solr search indexes
echo "rebuild solr search indexes ..."
ckan -c ${APP_DIR}/production.ini search-index rebuild

# set init flag to done
echo "$CKAN_IMAGE_TAG" > ${DATA_DIR}/.init-done
