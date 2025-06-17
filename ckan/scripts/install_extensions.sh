#!/bin/bash
set -e

echo "install_extensions ..."

pip install -e ${EXT_DIR}/ckanext-drupal8 \
    -e ${EXT_DIR}/ckanext-ytp_drupal \
    -e ${EXT_DIR}/ckanext-ytp_tasks \
    -e ${EXT_DIR}/ckanext-ytp_request \
    -e ${EXT_DIR}/ckanext-ytp_main \
    -e ${EXT_DIR}/ckanext-hierarchy \
    -e ${EXT_DIR}/ckanext-matomo \
    -e ${EXT_DIR}/ckanext-harvest \
    -e ${EXT_DIR}/ckanext-report \
    -e ${EXT_DIR}/ckanext-spatial \
    -e ${EXT_DIR}/ckanext-dcat \
    -e ${EXT_DIR}/ckanext-cloudstorage \
    -e ${EXT_DIR}/ckanext-scheming \
    -e ${EXT_DIR}/ckanext-fluent \
    -e ${EXT_DIR}/ckanext-showcase \
    -e ${EXT_DIR}/ckanext-sixodp_showcase \
    -e ${EXT_DIR}/ckanext-sixodp_showcasesubmit \
    -e ${EXT_DIR}/ckanext-geoview \
    -e ${EXT_DIR}/ckanext-pdfview \
    -e ${EXT_DIR}/ckanext-reminder \
    -e ${EXT_DIR}/ckanext-organizationapproval \
    -e ${EXT_DIR}/ckanext-advancedsearch \
    -e ${EXT_DIR}/ckanext-forcetranslation \
    -e ${EXT_DIR}/ckanext-apis \
    -e ${EXT_DIR}/ckanext-openapiviewer \
    -e ${EXT_DIR}/ckanext-statistics \
    -e ${EXT_DIR}/ckanext-sentry \
    -e ${EXT_DIR}/ckanext-sitesearch \
    -e ${EXT_DIR}/ckanext-archiver \
    -e ${EXT_DIR}/ckanext-qa \
    -e ${EXT_DIR}/ckanext-ytp_recommendation


# compile translations
(cd ${EXT_DIR}/ckanext-ytp_request; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-ytp_drupal; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-ytp_main; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-sixodp_showcase; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-report; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-organizationapproval; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-advancedsearch; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-scheming; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-statistics; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-matomo; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-ytp_recommendation; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-apis; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-harvest; python setup.py compile_catalog -f)
