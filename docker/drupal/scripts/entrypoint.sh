#!/bin/sh
set -e

# init database if not exists (return value is 0 and result is 0 rows)
echo "init_db() ..."

DB_CHECK_SQL="SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='node'"
DB_CHECK_RES=$(PGPASSWORD="${DB_DRUPAL_PASS}" psql -tA -h "${DB_HOST}" -U "${DB_DRUPAL_USER}" -d "${DB_DRUPAL}" -c "${DB_CHECK_SQL}")
if [ $? -eq 0 ] && [[ -z "${DB_CHECK_RES// }" ]]; then
  drush site:install -y standard \
    --db-url="pgsql://${DB_DRUPAL_USER}:${DB_DRUPAL_PASS}@${DB_HOST}:5432/${DB_DRUPAL}" \
    --account-name="${SYSADMIN_USER}" \
    --account-pass="${SYSADMIN_PASS}" \
    --account-mail="${SYSADMIN_EMAIL}" \
    --site-name="${SITE_NAME}"
fi

# run database upgrades & rebuild cache
drush updatedb -y --no-cache-clear
drush cache:rebuild

# init drupal if not done, otherwise run re-init
if [ ! -f /opt/drupal/web/.init-done ] && [ ! -f /opt/drupal/web/.init-lock ]; then
  flock -x /opt/drupal/web/.init-lock -c './init_drupal.sh'

  # set init flag to done
  touch /opt/drupal/web/.init-done
else
  # apply templates
  flock -x /opt/drupal/web/.init-lock -c './reinit_drupal.sh'
fi

# run php-fpm
docker-php-entrypoint php-fpm