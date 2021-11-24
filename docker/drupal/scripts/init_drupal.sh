#!/bin/bash
set -e

echo "init_drupal() ..."

# enable nginx maintenance mode
touch /var/www/resources/.init-progress

# init filesystems
. init_filesystems.sh

# init modules
. init_modules.sh

# init database if not exists (return value is 0 and result is 0 rows)
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

# apply jinja2 templates
jinja2 /opt/templates/settings.php.j2 -o /opt/drupal/web/sites/default/settings.php

# run database upgrades & rebuild cache
drush updatedb -y --no-cache-clear
drush cache:rebuild

# enable language modules, add languages and set default
drush pm:enable -y config_translation
drush pm:enable -y content_translation
drush pm:enable -y language
drush pm:enable -y locale
drush pm:enable -y drush_language
drush language:add -y "fi"
drush language:add -y "sv"
drush language:default -y "fi"

# enable base theme
drush theme:enable -y bootstrap

# uninstall disabled modules
drush pm:uninstall -y search
drush pm:uninstall -y contextual
drush pm:uninstall -y page_cache

# enable extra modules
drush pm:enable -y twig_tweak
drush pm:enable -y fontawesome_menu_icons
drush pm:enable -y smtp
drush pm:enable -y pathauto
drush pm:enable -y easy_breadcrumb
drush pm:enable -y twig_field_value
drush pm:enable -y disqus
drush pm:enable -y redirect
drush pm:enable -y search_api
drush pm:enable -y search_api_db
drush pm:enable -y search_api_db_defaults
drush pm:enable -y token
drush pm:enable -y metatag
drush pm:enable -y metatag_open_graph
drush pm:enable -y ape
drush pm:enable -y honeypot
drush pm:enable -y domain_registration
drush pm:enable -y protected_submissions
drush pm:enable -y recaptcha
drush pm:enable -y unpublished_node_permissions
drush pm:enable -y menu_item_role_access
drush pm:enable -y matomo
drush pm:enable -y upgrade_status

# enable custom modules
drush pm:enable -y avoindata_header
drush pm:enable -y avoindata_servicemessage
drush pm:enable -y avoindata_hero
drush pm:enable -y avoindata_categories
drush pm:enable -y avoindata_infobox
drush pm:enable -y avoindata_datasetlist
drush pm:enable -y avoindata_newsfeed
drush pm:enable -y avoindata_appfeed
drush pm:enable -y avoindata_footer
drush pm:enable -y avoindata_articles
drush pm:enable -y avoindata_events
drush pm:enable -y avoindata_guide
drush pm:enable -y avoindata_user
drush pm:enable -y avoindata_ckeditor_plugins

# remove some configurations
# NOTE: ansible role skips errors with this condition:
#       result.rc == 1 and 'Config {{ item }} does not exist' not in result.stderr
drush config:delete easy_breadcrumb.settings                            || true
drush config:delete node.type.page                                      || true
drush config:delete core.entity_form_display.node.page.default          || true
drush config:delete core.entity_view_display.node.page.default          || true
drush config:delete pathauto.settings                                   || true
drush config:delete captcha.captcha_point.contact_message_feedback_form || true
drush config:delete core.base_field_override.node.article.promote       || true
drush config:delete editor.editor.full_html                             || true
drush config:delete block.block.avoindata_collapsiblesearch             || true
drush config:delete block.block.avoindata_infobox                       || true

# enable custom theme + reload themes
drush theme:enable -y avoindata
drush config:set -y system.theme default avoindata
drush config:import -y --partial --source /opt/drupal/web/themes/avoindata/config/install

# reload custom modules
# NOTE: ansible role skips errors with this condition:
#       result.rc == 1 and 'The source directory does not exist. The source is not a directory.' not in result.stderr and 'already exists' not in result.stderr
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-header/config/install           || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-servicemessage/config/install   || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-hero/config/install             || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-categories/config/install       || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-infobox/config/install          || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-datasetlist/config/install      || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-newsfeed/config/install         || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-appfeed/config/install          || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-footer/config/install           || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-articles/config/install         || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-events/config/install           || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-guide/config/install            || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-user/config/install             || true
drush config:import -y --partial --source /opt/drupal/web/modules/avoindata-ckeditor-plugins/config/install || true

# apply jinja2 templates
jinja2 --format=yaml /opt/templates/site_config/disqus.settings.yml.j2    -o /opt/drupal/site_config/disqus.settings.yml
jinja2 --format=yaml /opt/templates/site_config/matomo.settings.yml.j2    -o /opt/drupal/site_config/matomo.settings.yml
jinja2 --format=yaml /opt/templates/site_config/recaptcha.settings.yml.j2 -o /opt/drupal/site_config/recaptcha.settings.yml
jinja2 --format=yaml /opt/templates/site_config/smtp.settings.yml.j2      -o /opt/drupal/site_config/smtp.settings.yml
jinja2 --format=yaml /opt/templates/site_config/update.settings.yml.j2    -o /opt/drupal/site_config/update.settings.yml

# disable captcha conditionally
if [ "${CAPTCHA_ENABLED}" != "true" ]; then
  rm -f /opt/drupal/site_config/captcha.settings.yml
  rm -f /opt/drupal/site_config/captcha.captcha_point.user_register_form.yml
  rm -f /opt/drupal/site_config/captcha.captcha_point.contact_message_event_form.yml
  rm -f /opt/drupal/site_config/captcha.captcha_point.contact_message_feedback_form.yml
fi

# import settings
drush config:import -y --partial --source /opt/drupal/site_config

# rebuild cache
drush cache:rebuild

# update translations
drush language:import:translations /opt/i18n/fi/drupal8.po     --langcode "fi"
drush language:import:translations /opt/i18n/sv/drupal8.po     --langcode "sv"
drush language:import:translations /opt/i18n/en_GB/drupal8.po  --langcode "en"

# init users and roles
python3 init_users.py

# make sure file permissions are correct
chown -R www-data:www-data /opt/drupal/web/sites/default/sync
chown -R www-data:www-data /opt/drupal/web/sites/default/files

# disable nginx maintenance mode
rm -f /var/www/resources/.init-progress

# set init flag to done
echo "$DRUPAL_IMAGE_VERSION" > /opt/drupal/web/.init-done