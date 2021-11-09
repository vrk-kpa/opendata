#!/bin/sh
set -e

# init drupal if not done, otherwise run re-init
if [ ! -f /opt/drupal/web/.init-done ]; then
  flock -s /opt/drupal/web/.init-lock -c './init_drupal.sh'

  # set init flag to done
  touch /opt/drupal/web/.init-done
else
  # apply templates
  flock -s /opt/drupal/web/.init-lock -c './reinit_drupal.sh'
fi

# run php-fpm
docker-php-entrypoint php-fpm