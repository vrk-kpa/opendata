#!/bin/bash
set -e

echo "install_extensions ..."

REQUIREMENTS_FILES="${EXT_DIR}/ckanext-drupal8/requirements.txt \
  ${EXT_DIR}/ckanext-ytp_drupal/requirements.txt \
  ${EXT_DIR}/ckanext-ytp_tasks/requirements.txt \
  ${EXT_DIR}/ckanext-ytp_request/requirements.txt \
  ${EXT_DIR}/ckanext-ytp_main/requirements.txt \
  ${EXT_DIR}/ckanext-hierarchy/requirements.txt \
  ${EXT_DIR}/ckanext-matomo/requirements.txt \
  ${EXT_DIR}/ckanext-datarequests/requirements.txt \
  ${EXT_DIR}/ckanext-harvest/requirements.txt \
  ${EXT_DIR}/ckanext-report/requirements.txt \
  ${EXT_DIR}/ckanext-spatial/requirements.txt \
  ${EXT_DIR}/ckanext-dcat/requirements.txt \
  ${EXT_DIR}/ckanext-cloudstorage/requirements.txt \
  ${EXT_DIR}/ckanext-scheming/requirements.txt \
  ${EXT_DIR}/ckanext-fluent/requirements.txt \
  ${EXT_DIR}/ckanext-showcase/requirements.txt \
  ${EXT_DIR}/ckanext-sixodp_showcase/requirements.txt \
  ${EXT_DIR}/ckanext-sixodp_showcasesubmit/requirements.txt \
  ${EXT_DIR}/ckanext-geoview/requirements.txt \
  ${EXT_DIR}/ckanext-pdfview/requirements.txt \
  ${EXT_DIR}/ckanext-disqus/requirements.txt \
  ${EXT_DIR}/ckanext-reminder/requirements.txt \
  ${EXT_DIR}/ckanext-archiver/requirements.txt \
  ${EXT_DIR}/ckanext-qa/requirements.txt \
  ${EXT_DIR}/ckanext-organizationapproval/requirements.txt \
  ${EXT_DIR}/ckanext-advancedsearch/requirements.txt \
  ${EXT_DIR}/ckanext-forcetranslation/requirements.txt \
  ${EXT_DIR}/ckanext-apis/requirements.txt \
  ${EXT_DIR}/ckanext-prh_tools/requirements.txt \
  ${EXT_DIR}/ckanext-openapiviewer/requirements.txt \
  ${EXT_DIR}/ckanext-statistics/requirements.txt \
  ${EXT_DIR}/ckanext-sentry/requirements.txt \
  ${EXT_DIR}/ckanext-sitesearch/requirements.txt \
  ${EXT_DIR}/ckanext-ytp_recommendation/requirements.txt \
  ${EXT_DIR}/ckanext-drupal8/pip-requirements.txt \
  ${EXT_DIR}/ckanext-ytp_drupal/pip-requirements.txt \
  ${EXT_DIR}/ckanext-ytp_tasks/pip-requirements.txt \
  ${EXT_DIR}/ckanext-ytp_request/pip-requirements.txt \
  ${EXT_DIR}/ckanext-ytp_main/pip-requirements.txt \
  ${EXT_DIR}/ckanext-hierarchy/pip-requirements.txt \
  ${EXT_DIR}/ckanext-matomo/pip-requirements.txt \
  ${EXT_DIR}/ckanext-datarequests/pip-requirements.txt \
  ${EXT_DIR}/ckanext-harvest/pip-requirements.txt \
  ${EXT_DIR}/ckanext-report/pip-requirements.txt \
  ${EXT_DIR}/ckanext-spatial/pip-requirements.txt \
  ${EXT_DIR}/ckanext-dcat/pip-requirements.txt \
  ${EXT_DIR}/ckanext-cloudstorage/pip-requirements.txt \
  ${EXT_DIR}/ckanext-scheming/pip-requirements.txt \
  ${EXT_DIR}/ckanext-fluent/pip-requirements.txt \
  ${EXT_DIR}/ckanext-showcase/pip-requirements.txt \
  ${EXT_DIR}/ckanext-sixodp_showcase/pip-requirements.txt \
  ${EXT_DIR}/ckanext-sixodp_showcasesubmit/pip-requirements.txt \
  ${EXT_DIR}/ckanext-geoview/pip-requirements.txt \
  ${EXT_DIR}/ckanext-pdfview/pip-requirements.txt \
  ${EXT_DIR}/ckanext-disqus/pip-requirements.txt \
  ${EXT_DIR}/ckanext-reminder/pip-requirements.txt \
  ${EXT_DIR}/ckanext-archiver/pip-requirements.txt \
  ${EXT_DIR}/ckanext-qa/pip-requirements.txt \
  ${EXT_DIR}/ckanext-organizationapproval/pip-requirements.txt \
  ${EXT_DIR}/ckanext-advancedsearch/pip-requirements.txt \
  ${EXT_DIR}/ckanext-forcetranslation/pip-requirements.txt \
  ${EXT_DIR}/ckanext-apis/pip-requirements.txt \
  ${EXT_DIR}/ckanext-prh_tools/pip-requirements.txt \
  ${EXT_DIR}/ckanext-openapiviewer/pip-requirements.txt \
  ${EXT_DIR}/ckanext-statistics/pip-requirements.txt \
  ${EXT_DIR}/ckanext-sentry/pip-requirements.txt \
  ${EXT_DIR}/ckanext-sitesearch/pip-requirements.txt \
  ${EXT_DIR}/ckanext-ytp_recommendation/pip-requirements.txt"

echo "Missing but configured requirements files:"
EXISTING_REQUIREMENTS_FILES=$(ls -d $REQUIREMENTS_FILES | cat -)
echo "Installing: $EXISTING_REQUIREMENTS_FILES"
pip install $(for item in $EXISTING_REQUIREMENTS_FILES; do echo "-r $item"; done)

# install extensions
pip install -e ${EXT_DIR}/ckanext-drupal8 \
    -e ${EXT_DIR}/ckanext-ytp_drupal \
    -e ${EXT_DIR}/ckanext-ytp_tasks \
    -e ${EXT_DIR}/ckanext-ytp_request \
    -e ${EXT_DIR}/ckanext-ytp_main \
    -e ${EXT_DIR}/ckanext-hierarchy \
    -e ${EXT_DIR}/ckanext-matomo \
    -e ${EXT_DIR}/ckanext-datarequests \
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
    -e ${EXT_DIR}/ckanext-disqus \
    -e ${EXT_DIR}/ckanext-reminder \
    -e ${EXT_DIR}/ckanext-organizationapproval \
    -e ${EXT_DIR}/ckanext-advancedsearch \
    -e ${EXT_DIR}/ckanext-forcetranslation \
    -e ${EXT_DIR}/ckanext-apis \
    -e ${EXT_DIR}/ckanext-prh_tools \
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
(cd ${EXT_DIR}/ckanext-datarequests; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-matomo; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-ytp_recommendation; python setup.py compile_catalog -f)
(cd ${EXT_DIR}/ckanext-apis; python setup.py compile_catalog -f)
