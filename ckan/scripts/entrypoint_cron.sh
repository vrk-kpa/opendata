#!/bin/bash
set -e

echo "entrypoint_cron ..."

# Copy app from readonly copy to tmpfs mount
cp -Rn ${APP_DIR}_readonly/* ${APP_DIR}

# wait for ckan to initialize properly
while [[ "$(cat ${DATA_DIR}/.init-done)" != "$CKAN_IMAGE_TAG" ]]; do
  echo "entrypoint_cron - waiting for .init-done flag to be set ..."
  sleep 1s
done

# install extensions (DEV_MODE)
if [[ "${DEV_MODE}" == "true" ]]; then
  echo "entrypoint_cron - installing extensions because DEV_MODE = 'true' ..."
  sudo -E ${SCRIPT_DIR}/install_extensions.sh
  sudo -E ${SCRIPT_DIR}/install_extension_requirements.sh
fi

# apply templates
jinja2 ${TEMPLATE_DIR}/production.ini.j2 -o ${APP_DIR}/production.ini
jinja2 ${TEMPLATE_DIR}/who.ini.j2 -o ${APP_DIR}/who.ini
jinja2 ${TEMPLATE_DIR}/datastore_permissions.sql.j2 -o ${SCRIPT_DIR}/datastore_permissions.sql

# export environment for cron
printenv | sed 's/=\(.*\)/="\1"/' > ${CRON_DIR}/.environment

# run supervisord
supervisord --configuration ${SUPERV_DIR}/supervisord.conf &
# run supercronic
supercronic ${CRON_DIR}/crontab
