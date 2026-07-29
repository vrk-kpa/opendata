#!/bin/bash
set -e

echo "entrypoint ..."

# init drupal if not done or version updated, otherwise run re-init
flock -x ${DATA_DIR}/.init-lock -c 'echo "waiting for .init-lock to be released ..."'
if [[ "$(cat ${DATA_DIR}/.init-done)" != "$DRUPAL_IMAGE_TAG" ]]; then
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/init_drupal.sh'
else
  flock -x ${DATA_DIR}/.init-lock -c '${SCRIPT_DIR}/reinit_drupal.sh'
fi

# run supervisord which runs php-fpm and nginx
docker-php-entrypoint supervisord -n -c /etc/supervisord.conf
