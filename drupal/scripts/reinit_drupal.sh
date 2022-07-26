#!/bin/bash
set -e

echo "reinit_drupal ..."

# apply jinja2 templates
jinja2 ${TEMPLATE_DIR}/settings.php.j2 -o ${SITE_DIR}/default/settings.php
jinja2 ${TEMPLATE_DIR}/services.yml.j2 -o ${SITE_DIR}/default/services.yml

# rebuild cache
drush cache:rebuild

# init local development related stuff
if [[ "${DEV_MODE}" == "true" ]]; then
  # apply jinja2 templates
  jinja2 ${TEMPLATE_DIR}/settings.local.php.j2 -o ${SITE_DIR}/default/settings.local.php
  jinja2 ${TEMPLATE_DIR}/development.services.yml.j2 -o ${SITE_DIR}/development.services.yml
  
  # enable devel module
  drush pm:enable -y devel
fi

# apply jinja2 templates
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/disqus.settings.yml.j2    -o ${APP_DIR}/site_config/disqus.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/matomo.settings.yml.j2    -o ${APP_DIR}/site_config/matomo.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/recaptcha.settings.yml.j2 -o ${APP_DIR}/site_config/recaptcha.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/smtp.settings.yml.j2      -o ${APP_DIR}/site_config/smtp.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/update.settings.yml.j2    -o ${APP_DIR}/site_config/update.settings.yml

# disable captcha conditionally
if [ "${CAPTCHA_ENABLED}" != "true" ]; then
  rm -f ${APP_DIR}/site_config/captcha.settings.yml
  rm -f ${APP_DIR}/site_config/captcha.captcha_point.user_register_form.yml
  rm -f ${APP_DIR}/site_config/captcha.captcha_point.contact_message_event_form.yml
  rm -f ${APP_DIR}/site_config/captcha.captcha_point.contact_message_feedback_form.yml
fi

# import settings
drush config:import -y --partial --source ${APP_DIR}/site_config

# rebuild cache
drush cache:rebuild
