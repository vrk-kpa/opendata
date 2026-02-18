#!/bin/bash
set -e

echo "install_extension_requirements ..."

pip_install() {
  if [[ ! -f "$1" ]]; then
    echo "pip_install: skipping $1 because file does not exist!"
    return 0
  fi

  echo "pip_install: installing $1 ..."

  pip install -r "$1"
}

# install extension requirements
pip_install "${EXT_DIR}/ckanext-forcetranslation/requirements.txt"
pip_install "${EXT_DIR}/ckanext-archiver/requirements.txt"
pip_install "${EXT_DIR}/ckanext-dcat/requirements.txt"
pip_install "${EXT_DIR}/ckanext-drupal8/requirements.txt"
pip_install "${EXT_DIR}/ckanext-hierarchy/requirements.txt"
pip_install "${EXT_DIR}/ckanext-spatial/requirements.txt"
pip_install "${EXT_DIR}/ckanext-statistics/requirements.txt"
pip_install "${EXT_DIR}/ckanext-matomo/requirements.txt"
pip_install "${EXT_DIR}/ckanext-fluent/requirements.txt"
pip_install "${EXT_DIR}/ckanext-qa/requirements.txt"
pip_install "${EXT_DIR}/ckanext-showcase/requirements.txt"
pip_install "${EXT_DIR}/ckanext-report/requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcase/requirements.txt"
pip_install "${EXT_DIR}/ckanext-sixodp_showcasesubmit/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_tasks/requirements.txt"
pip_install "${EXT_DIR}/ckanext-harvest/requirements.txt"
pip_install "${EXT_DIR}/ckanext-cloudstorage/requirements.txt"
pip_install "${EXT_DIR}/ckanext-organizationapproval/requirements.txt"
pip_install "${EXT_DIR}/ckanext-advancedsearch/requirements.txt"
pip_install "${EXT_DIR}/ckanext-apis/requirements.txt"
pip_install "${EXT_DIR}/ckanext-ytp_main/requirements.txt"
