#!/bin/sh
set -e

echo "reinit_drupal() ..."

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