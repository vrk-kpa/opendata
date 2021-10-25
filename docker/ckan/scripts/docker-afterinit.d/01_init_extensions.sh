#!/bin/bash
set -ex

# add facet translations
paster --plugin=ckanext-ytp_main ytp-facet-translations ${EXT_DIR}/ckanext-ytp_main/ckanext/ytp/i18n -c ${APP_DIR}/production.ini

# create vocabularies
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_platform_vocabulary -c ${APP_DIR}/production.ini
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_showcase_type_vocabulary -c ${APP_DIR}/production.ini

# upgrade filestore
paster --plugin=ckan db migrate-filestore -c ${APP_DIR}/production.ini

# initialize extension databases
[[ "${CKAN_PLUGINS}" == *"ytp_request"* ]]  && paster --plugin=ckanext-ytp_request initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"harvest"* ]]      && paster --plugin=ckanext-harvest harvester initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"ytp_spatial"* ]]  && paster --plugin=ckanext-spatial spatial initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"archiver"* ]]     && paster --plugin=ckanext-archiver archiver init -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"qa"* ]]           && paster --plugin=ckanext-qa qa init -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"report"* ]]       && paster --plugin=ckanext-report report initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"matomo"* ]]       && paster --plugin=ckanext-matomo matomo init_db -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"cloudstorage"* ]] && paster --plugin=ckanext-cloudstorage cloudstorage initdb -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"rating"* ]]       && paster --plugin=ckanext-rating rating init -c ${APP_DIR}/production.ini
[[ "${CKAN_PLUGINS}" == *"reminder"* ]]     && paster --plugin=ckanext-reminder reminder init -c ${APP_DIR}/production.ini
