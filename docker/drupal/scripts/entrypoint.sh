#!/bin/bash
set -e

echo "entrypoint() ..."

# init drupal if not done or version updated, otherwise run re-init
flock -x /opt/drupal/web/.init-lock -c 'echo "waiting for .init-lock to be released ..."'
if [[ "$(cat /opt/drupal/web/.init-done)" != "$DRUPAL_IMAGE_VERSION" ]]; then
  flock -x /opt/drupal/web/.init-lock -c './init_drupal.sh'
else
  flock -x /opt/drupal/web/.init-lock -c './reinit_drupal.sh'
fi

# run php-fpm
docker-php-entrypoint php-fpm