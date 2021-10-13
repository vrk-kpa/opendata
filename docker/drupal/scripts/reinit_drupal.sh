#!/bin/sh
set -e

echo "reinit_drupal() ..."

# always init modules first
. init_modules.sh

# run database upgrades & rebuild cache
drush updatedb -y --no-cache-clear
drush cache:rebuild

# apply jinja2 templates
jinja2 --format=yaml /opt/templates/site_config/disqus.settings.yml.j2    -o /opt/drupal/site_config/disqus.settings.yml
jinja2 --format=yaml /opt/templates/site_config/matomo.settings.yml.j2    -o /opt/drupal/site_config/matomo.settings.yml
jinja2 --format=yaml /opt/templates/site_config/recaptcha.settings.yml.j2 -o /opt/drupal/site_config/recaptcha.settings.yml
jinja2 --format=yaml /opt/templates/site_config/smtp.settings.yml.j2      -o /opt/drupal/site_config/smtp.settings.yml
jinja2 --format=yaml /opt/templates/site_config/update.settings.yml.j2    -o /opt/drupal/site_config/update.settings.yml

# import settings
drush config:import -y --partial --source /opt/drupal/site_config

# rebuild cache
drush cache:rebuild