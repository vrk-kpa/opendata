#!/bin/bash
set -e

echo "entrypoint_ckan ..."

# set env vars for base image prerun.py script
export CKAN_SQLALCHEMY_URL="postgresql://${DB_CKAN_USER}:${DB_CKAN_PASS}@${DB_CKAN_HOST}/${DB_CKAN}"
export CKAN_SOLR_URL="http://${SOLR_HOST}:${SOLR_PORT}/${SOLR_PATH}"
export CKAN_SYSADMIN_NAME="${SYSADMIN_USER}"
export CKAN_SYSADMIN_PASSWORD="${SYSADMIN_PASS}"
export CKAN_SYSADMIN_EMAIL="${SYSADMIN_EMAIL}"

# install extensions (DEV_MODE)
if [[ "${DEV_MODE}" == "true" ]]; then
    echo "entrypoint_ckan - installing extensions because DEV_MODE = 'true' ..."
    sudo -E ${SCRIPT_DIR}/install_extensions.sh
    echo "entrypoint_ckan - extensions installed"
fi

# init ckan if not done or version updated, otherwise run re-init
flock -x ${DATA_DIR}/.init-lock -c 'echo "waiting for .init-lock to be released ..."'
echo "entrypoint_ckan - initializing CKAN"
if [[ "$(cat ${DATA_DIR}/.init-done)" != "$CKAN_IMAGE_TAG" ]]; then
  echo "entrypoint_ckan - running init_ckan.sh"
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/init_ckan.sh'
else
  echo "entrypoint_ckan - running reinit_ckan.sh"
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/reinit_ckan.sh'
fi

echo "entrypoint_ckan - running CKAN"
# run uwsgi or ckan run
if [[ "${DEV_MODE}" != "true" ]]; then
  echo "entrypoint_ckan - running in PRODUCTION mode via uwsgi ..."
  uwsgi -i /srv/app/ckan-uwsgi.ini
else
  echo "entrypoint_ckan - running in DEVELOPMENT mode via ckan ..."
  ckan -c /srv/app/production.ini run --host 0.0.0.0 --prefix /data
fi
echo "entrypoint_ckan - exiting"
