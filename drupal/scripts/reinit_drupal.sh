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

  # enable dev mode
  drupal site:mode dev
fi

# apply jinja2 templates
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/matomo.settings.yml.j2    -o ${APP_DIR}/site_config/matomo.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/recaptcha.settings.yml.j2 -o ${APP_DIR}/site_config/recaptcha.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/smtp.settings.yml.j2      -o ${APP_DIR}/site_config/smtp.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/update.settings.yml.j2    -o ${APP_DIR}/site_config/update.settings.yml
jinja2 --format=yaml ${TEMPLATE_DIR}/site_config/raven.settings.yml.j2    -o ${APP_DIR}/site_config/raven.settings.yml

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

# update translations (if file has changed, otherwise skip)
SHA1_I18N_FI=$(sha1sum ${I18N_DIR}/fi/drupal.po)
if [[ "$SHA1_I18N_FI" != "$(cat ${DATA_DIR}/.sha1_18n_fi)" ]]; then
  drush language:import:translations ${I18N_DIR}/fi/drupal.po --langcode "fi"
  echo "$SHA1_I18N_FI" > ${DATA_DIR}/.sha1_18n_fi
else
  echo "skipping import of 'fi' i18n because file hasn't changed ..."
fi

SHA1_I18N_SV=$(sha1sum ${I18N_DIR}/sv/drupal.po)
if [[ "$SHA1_I18N_SV" != "$(cat ${DATA_DIR}/.sha1_18n_sv)" ]]; then
  drush language:import:translations ${I18N_DIR}/sv/drupal.po --langcode "sv"
  echo "$SHA1_I18N_SV" > ${DATA_DIR}/.sha1_18n_sv
else
  echo "skipping import of 'sv' i18n because file hasn't changed ..."
fi

SHA1_I18N_EN=$(sha1sum ${I18N_DIR}/en_GB/drupal.po)
if [[ "$SHA1_I18N_EN" != "$(cat ${DATA_DIR}/.sha1_18n_en)" ]]; then
  drush language:import:translations ${I18N_DIR}/en_GB/drupal.po --langcode "en"
  echo "$SHA1_I18N_EN" > ${DATA_DIR}/.sha1_18n_en
else
  echo "skipping import of 'en' i18n because file hasn't changed ..."
fi
