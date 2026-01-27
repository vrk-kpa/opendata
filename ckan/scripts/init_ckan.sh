#!/bin/bash
set -e

echo "init_ckan ..."

# synchronize persistent data files
rsync -au ${DATA_DIR}_base/. ${DATA_DIR}

# apply templates
jinja2 ${TEMPLATE_DIR}/ckan.ini.j2 -o ${APP_DIR}/ckan.ini
jinja2 ${TEMPLATE_DIR}/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${TEMPLATE_DIR}/ckan-uwsgi.ini.j2 -o ${APP_DIR}/ckan-uwsgi.ini
jinja2 ${TEMPLATE_DIR}/datastore_permissions.sql.j2 -o ${SCRIPT_DIR}/datastore_permissions.sql

# run prerun script that checks connections and inits db
python connection_check.py || { echo '[CKAN connection check] FAILED. Exiting...' ; exit 1; }

echo "Init CKAN database ..."
ckan -c ${APP_DIR}/ckan.ini db init

bash ${SCRIPT_DIR}/upgrade_ckan_database.sh

# execute SQL scripts
echo "Modify datastore permissions ..."
cat ${SCRIPT_DIR}/datastore_permissions.sql | PGPASSWORD="${DB_DATASTORE_ADMIN_PASS}" psql -d ${DB_DATASTORE} -h ${DB_DATASTORE_HOST} -U ${DB_DATASTORE_ADMIN} --set ON_ERROR_STOP=1

# init ckan extensions
echo "init ckan extensions ..."
#ckan -c ${APP_DIR}/ckan.ini opendata add-facet-translations ${EXT_DIR}/ckanext-ytp_main/ckanext/ytp/i18n
ckan -c ${APP_DIR}/ckan.ini sixodp-showcase create_platform_vocabulary

echo "Generate JavaScript translations"
ckan -c ${APP_DIR}/ckan.ini translation js

# Import municipality data
ckan -c ${APP_DIR}/ckan.ini opendata-model populate-municipality-bounding-box

# set init flag to done
echo "$CKAN_IMAGE_TAG" > ${DATA_DIR}/.init-done
