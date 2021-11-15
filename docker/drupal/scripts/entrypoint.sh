#!/bin/sh
set -e

# init drupal if not done or version updated, otherwise run re-init
if [[ "$(cat /opt/drupal/web/.init-done)" != "$DRUPAL_IMAGE_VERSION" ]]; then
  flock -x /opt/drupal/web/.init-lock -c './init_drupal.sh'

  # set init flag to done
  echo "$DRUPAL_IMAGE_VERSION" > /opt/drupal/web/.init-done
else
  flock -x /opt/drupal/web/.init-lock -c './reinit_drupal.sh'
fi

# run php-fpm
docker-php-entrypoint php-fpm