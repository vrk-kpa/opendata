#!/bin/bash
set -e

echo "entrypoint ..."

# Copy readonly copy of the app onto the tmpfs mounted on top of the app dir
cp -aRn ${APP_DIR}_readonly/* ${APP_DIR}/

# init drupal if not done or version updated, otherwise run re-init
flock -x ${DATA_DIR}/.init-lock -c 'echo "waiting for .init-lock to be released ..."'
if [[ "$(cat ${DATA_DIR}/.init-done)" != "$DRUPAL_IMAGE_TAG" ]]; then
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/init_drupal.sh'
else
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/reinit_drupal.sh'
fi

# run php-fpm
docker-php-entrypoint apache2-foreground
