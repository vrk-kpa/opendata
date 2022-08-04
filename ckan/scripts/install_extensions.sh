#!/bin/bash
set -e

echo "install_extensions ..."

pip_install() {
  if [[ ! -f "$1" ]]; then
    echo "pip_install: skipping $1 because file does not exist!"
    return 0
  fi

  echo "pip_install: installing $1 ..."

  pip install -r "$1"
}

# install extension requirements
pip_install "${EXT_DIR}/ckanext-drupal8/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_drupal/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_tasks/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_request/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_main/requirements.txt"
pip_install "${EXT_DIR}/ckanext-hierarchy/requirements.txt"
pip_install "${EXT_DIR}/ckanext-matomo/requirements.txt"
pip_install "${EXT_DIR}/ckanext-datarequests/requirements.txt"
pip_install "${EXT_DIR}/ckanext-harvest/requirements.txt"
pip_install "${EXT_DIR}/ckanext-report/requirements.txt"
pip_install "${EXT_DIR}/ckanext-spatial/requirements.txt"
pip_install "${EXT_DIR}/ckanext-dcat/requirements.txt"
pip_install "${EXT_DIR}/ckanext-cloudstorage/requirements.txt"
pip_install "${EXT_DIR}/ckanext-scheming/requirements.txt"
pip_install "${EXT_DIR}/ckanext-fluent/requirements.txt"
pip_install "${EXT_DIR}/ckanext-showcase/requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcase/requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcasesubmit/requirements.txt"
pip_install "${EXT_DIR}/ckanext-geoview/requirements.txt"
pip_install "${EXT_DIR}/ckanext-pdfview/requirements.txt"
pip_install "${EXT_DIR}/ckanext-disqus/requirements.txt"
pip_install "${EXT_DIR}/ckanext-reminder/requirements.txt"
#pip_install "${EXT_DIR}/ckanext-archiver/requirements.txt"
#pip_install "${EXT_DIR}/ckanext-qa/requirements.txt"
pip_install "${EXT_DIR}/ckanext-organizationapproval/requirements.txt"
pip_install "${EXT_DIR}/ckanext-advancedsearch/requirements.txt"
pip_install "${EXT_DIR}/ckanext-forcetranslation/requirements.txt"
pip_install "${EXT_DIR}/ckanext-apis/requirements.txt"
pip_install "${EXT_DIR}/ckanext-prh_tools/requirements.txt"
pip_install "${EXT_DIR}/ckanext-openapiviewer/requirements.txt"
pip_install "${EXT_DIR}/ckanext-statistics/requirements.txt"
pip_install "${EXT_DIR}/ckanext-sentry/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_recommendation/requirements.txt"

# install extension pip requirements
pip_install "${EXT_DIR}/ckanext-drupal8/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_drupal/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_tasks/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_request/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_main/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-hierarchy/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-matomo/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-datarequests/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-harvest/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-report/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-spatial/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-dcat/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-cloudstorage/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-scheming/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-fluent/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-showcase/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcase/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcasesubmit/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-geoview/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-pdfview/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-disqus/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-reminder/pip-requirements.txt"
#pip_install "${EXT_DIR}/ckanext-archiver/pip-requirements.txt"
#pip_install "${EXT_DIR}/ckanext-qa/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-organizationapproval/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-advancedsearch/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-forcetranslation/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-apis/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-prh_tools/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-openapiviewer/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-statistics/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-sentry/pip-requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_recommendation/pip-requirements.txt"

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
    -e ${EXT_DIR}/ckanext-ytp_recommendation

    #-e ${EXT_DIR}/ckanext-archiver \
    #-e ${EXT_DIR}/ckanext-qa \

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
