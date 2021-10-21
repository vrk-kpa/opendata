#!/bin/bash
set -e

# add facet translations
paster --plugin=ckanext-ytp_main ytp-facet-translations ${EXT_DIR}/ckanext-ytp_main/ckanext/ytp/i18n -c ${APP_DIR}/production.ini

# create vocabularies
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_platform_vocabulary -c ${APP_DIR}/production.ini
paster --plugin=ckanext-sixodp_showcase sixodp_showcase create_showcase_type_vocabulary -c ${APP_DIR}/production.ini
