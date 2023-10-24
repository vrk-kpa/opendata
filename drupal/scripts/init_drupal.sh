#!/bin/bash
set -e

echo "init_drupal ..."

# init database if not exists (return value is 0 and result is 0 rows)
DB_CHECK_SQL="SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='node'"
DB_CHECK_RES=$(PGPASSWORD="${DB_DRUPAL_PASS}" psql -tA -h "${DB_DRUPAL_HOST}" -U "${DB_DRUPAL_USER}" -d "${DB_DRUPAL}" -c "${DB_CHECK_SQL}")
if [ $? -eq 0 ] && [[ -z "${DB_CHECK_RES}" ]]; then
  drush site:install -y standard \
    --db-url="pgsql://${DB_DRUPAL_USER}:${DB_DRUPAL_PASS}@${DB_DRUPAL_HOST}:5432/${DB_DRUPAL}" \
    --account-name="${SYSADMIN_USER}" \
    --account-pass="${SYSADMIN_PASS}" \
    --account-mail="${SYSADMIN_EMAIL}" \
    --site-name="${SITE_NAME}"
fi

# apply jinja2 templates
jinja2 ${TEMPLATE_DIR}/settings.php.j2 -o ${SITE_DIR}/default/settings.php
jinja2 ${TEMPLATE_DIR}/services.yml.j2 -o ${SITE_DIR}/default/services.yml

# run database upgrades & rebuild cache
echo "upgrade database.."
drush updatedb -y --no-cache-clear
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

# get current modules
MODULE_INFO=$(drush pm:list --status enabled --field=name)

# enable language modules
echo "enable language modules.."
[[ "$MODULE_INFO" != *"config_translation"* ]]  && drush pm:enable -y config_translation
[[ "$MODULE_INFO" != *"content_translation"* ]] && drush pm:enable -y content_translation
[[ "$MODULE_INFO" != *"language"* ]]            && drush pm:enable -y language
[[ "$MODULE_INFO" != *"locale"* ]]              && drush pm:enable -y locale
[[ "$MODULE_INFO" != *"drush_language"* ]]      && drush pm:enable -y drush_language

# get current languages
LANG_INFO=$(drush language-info --field=language)

# add languages and set 'fi' as default
[[ "$LANG_INFO" != *"Finnish"* ]] && drush language:add -y "fi"
[[ "$LANG_INFO" != *"Swedish"* ]] && drush language:add -y "sv"
drush language:default -y "fi"

# enable base theme
drush theme:enable -y bootstrap

# remove some configurations
# NOTE: ansible role skips errors with this condition:
#       result.rc == 1 and 'Config {{ item }} does not exist' not in result.stderr
echo "delete configurations.."
drush config:delete easy_breadcrumb.settings                                       || true
drush config:delete node.type.page                                                 || true
drush config:delete core.entity_form_display.node.page.default                     || true
drush config:delete core.entity_view_display.node.page.default                     || true
drush config:delete pathauto.settings                                              || true
drush config:delete captcha.captcha_point.contact_message_feedback_form            || true
drush config:delete core.base_field_override.node.article.promote                  || true
drush config:delete editor.editor.full_html                                        || true
drush config:delete block.block.avoindata_collapsiblesearch                        || true
drush config:delete block.block.avoindata_infobox                                  || true
drush config:delete disqus.settings                                                || true
drush config:delete field.field.node.avoindata_guide_page.field_guide_comments     || true
drush config:delete field.field.node.avoindata_article.field_article_comments      || true
drush config:delete field.field.node.avoindata_event.field_event_comments          || true
drush config:delete field.storage.node.field_article_comments                      || true
drush config:delete field.storage.node.field_basic_page_comments                   || true
drush config:delete field.storage.node.field_event_comments                        || true
drush config:delete field.storage.node.field_guide_comments                        || true
drush config:delete core.entity_view_display.node.page.search_index                || true
drush config:delete core.entity_view_display.node.page.search_result               || true
drush config:delete core.entity_view_display.node.page.teaser                      || true
drush config:delete field.field.node.page.field_basic_page_comments                || true
drush config:delete field.storage.node.field_basic_page_comments                   || true
drush config:delete user.role.editor                                               || true
drush config:delete system.action.user_add_role_action.editor                      || true
drush config:delete system.action.user_remove_role_action.editor                   || true
drush config:delete node.type.article                                              || true
drush config:delete core.entity_form_display.node.article.default                  || true
drush config:delete core.entity_view_display.node.article.default                  || true
drush config:delete core.entity_view_display.node.article.rss                      || true
drush config:delete core.entity_view_display.node.article.search_index             || true
drush config:delete core.entity_view_display.node.article.search_result            || true
drush config:delete core.entity_view_display.node.article.teaser                   || true
drush config:delete field.field.node.article.body                                  || true
drush config:delete field.field.node.article.comment                               || true
drush config:delete field.field.node.article.field_image                           || true
drush config:delete field.field.node.article.field_tags                            || true
drush config:delete user.role.content_editor                                       || true
drush config:delete system.action.user_add_role_action.content_editor              || true
drush config:delete system.action.user_remove_role_action.content_editor           || true



# uninstall modules
echo "uninstall modules.."
[[ "$MODULE_INFO" == *"search"* ]]      && drush pm:uninstall -y search
[[ "$MODULE_INFO" == *"contextual"* ]]  && drush pm:uninstall -y contextual
[[ "$MODULE_INFO" == *"page_cache"* ]]  && drush pm:uninstall -y page_cache
[[ "$MODULE_INFO" == *"protected_submissions"* ]]  && drush pm:uninstall -y protected_submissions
[[ "$MODULE_INFO" == *"avoindata_infobox"* ]]  && drush pm:uninstall -y avoindata_infobox
[[ "$MODULE_INFO" == *"avoindata_ckeditor_plugins"* ]]  && drush pm:uninstall -y avoindata_ckeditor_plugins
[[ "$MODULE_INFO" == *"ckeditor"* ]]  && drush pm:uninstall -y ckeditor
[[ "$MODULE_INFO" == *"color"* ]]  && drush pm:uninstall -y color
[[ "$MODULE_INFO" == *"rdf"* ]]  && drush pm:uninstall -y rdf
[[ "$MODULE_INFO" == *"bartik"* ]]  && drush pm:uninstall -y bartik
[[ "$MODULE_INFO" == *"seven"* ]]  && drush pm:uninstall -y seven

# enable modules
echo "enable modules.."
[[ "$MODULE_INFO" != *"twig_tweak"* ]]                    && drush pm:enable -y twig_tweak
[[ "$MODULE_INFO" != *"fontawesome_menu_icons"* ]]        && drush pm:enable -y fontawesome_menu_icons
[[ "$MODULE_INFO" != *"smtp"* ]]                          && drush pm:enable -y smtp
[[ "$MODULE_INFO" != *"pathauto"* ]]                      && drush pm:enable -y pathauto
[[ "$MODULE_INFO" != *"easy_breadcrumb"* ]]               && drush pm:enable -y easy_breadcrumb
[[ "$MODULE_INFO" != *"twig_field_value"* ]]              && drush pm:enable -y twig_field_value
[[ "$MODULE_INFO" != *"redirect"* ]]                      && drush pm:enable -y redirect
[[ "$MODULE_INFO" != *"search_api"* ]]                    && drush pm:enable -y search_api
[[ "$MODULE_INFO" != *"search_api_db"* ]]                 && drush pm:enable -y search_api_db
[[ "$MODULE_INFO" != *"search_api_db_defaults"* ]]        && drush pm:enable -y search_api_db_defaults
[[ "$MODULE_INFO" != *"token"* ]]                         && drush pm:enable -y token
[[ "$MODULE_INFO" != *"metatag"* ]]                       && drush pm:enable -y metatag
[[ "$MODULE_INFO" != *"metatag_open_graph"* ]]            && drush pm:enable -y metatag_open_graph
[[ "$MODULE_INFO" != *"ape"* ]]                           && drush pm:enable -y ape
[[ "$MODULE_INFO" != *"honeypot"* ]]                      && drush pm:enable -y honeypot
[[ "$MODULE_INFO" != *"domain_registration"* ]]           && drush pm:enable -y domain_registration
[[ "$MODULE_INFO" != *"protected_forms"* ]]               && drush pm:enable -y protected_forms
[[ "$MODULE_INFO" != *"recaptcha"* ]]                     && drush pm:enable -y recaptcha
[[ "$MODULE_INFO" != *"unpublished_node_permissions"* ]]  && drush pm:enable -y unpublished_node_permissions
[[ "$MODULE_INFO" != *"menu_item_role_access"* ]]         && drush pm:enable -y menu_item_role_access
[[ "$MODULE_INFO" != *"matomo"* ]]                        && drush pm:enable -y matomo
[[ "$MODULE_INFO" != *"upgrade_status"* ]]                && drush pm:enable -y upgrade_status
[[ "$MODULE_INFO" != *"imce"* ]]                          && drush pm:enable -y imce
[[ "$MODULE_INFO" != *"transliterate_filenames"* ]]       && drush pm:enable -y transliterate_filenames
[[ "$MODULE_INFO" != *"password_policy"* ]]               && drush pm:enable -y password_policy
[[ "$MODULE_INFO" != *"password_policy_character_types"* ]] && drush pm:enable -y password_policy_character_types
[[ "$MODULE_INFO" != *"password_policy_length"* ]]        && drush pm:enable -y password_policy_length
[[ "$MODULE_INFO" != *"raven"* ]]                         && drush pm:enable -y raven
[[ "$MODULE_INFO" != *"menu_link_attributes"* ]]          && drush pm:enable -y menu_link_attributes

# remove some configurations
# NOTE: ansible role skips errors with this condition:
#       result.rc == 1 and 'Config {{ item }} does not exist' not in result.stderr
echo "delete configurations.."
drush config:delete easy_breadcrumb.settings                                       || true
drush config:delete node.type.page                                                 || true
drush config:delete core.entity_form_display.node.page.default                     || true
drush config:delete core.entity_view_display.node.page.default                     || true
drush config:delete core.base_field_override.node.page.promote                     || true
drush config:delete field.field.node.page.body                                     || true
drush config:delete pathauto.settings                                              || true
drush config:delete captcha.captcha_point.contact_message_feedback_form            || true
drush config:delete core.base_field_override.node.article.promote                  || true
drush config:delete editor.editor.full_html                                        || true

# enable custom modules
echo "enable custom modules.."
[[ "$MODULE_INFO" != *"avoindata_header"* ]]            && drush pm:enable -y avoindata_header
[[ "$MODULE_INFO" != *"avoindata_servicemessage"* ]]    && drush pm:enable -y avoindata_servicemessage
[[ "$MODULE_INFO" != *"avoindata_hero"* ]]              && drush pm:enable -y avoindata_hero
[[ "$MODULE_INFO" != *"avoindata_categories"* ]]        && drush pm:enable -y avoindata_categories
[[ "$MODULE_INFO" != *"avoindata_explore"* ]]           && drush pm:enable -y avoindata_explore
[[ "$MODULE_INFO" != *"avoindata_newsfeed"* ]]          && drush pm:enable -y avoindata_newsfeed
[[ "$MODULE_INFO" != *"avoindata_footer"* ]]            && drush pm:enable -y avoindata_footer
[[ "$MODULE_INFO" != *"avoindata_articles"* ]]          && drush pm:enable -y avoindata_articles
[[ "$MODULE_INFO" != *"avoindata_events"* ]]            && drush pm:enable -y avoindata_events
[[ "$MODULE_INFO" != *"avoindata_guide"* ]]             && drush pm:enable -y avoindata_guide
[[ "$MODULE_INFO" != *"avoindata_user"* ]]              && drush pm:enable -y avoindata_user
[[ "$MODULE_INFO" != *"avoindata_ckeditor5_plugins"* ]]  && drush pm:enable -y avoindata_ckeditor5_plugins

# enable custom theme + reload themes
echo "enable theme and install theme configurations.."
drush theme:enable -y avoindata
drush config:set -y system.theme default avoindata
drush config:import -y --partial --source ${THEME_DIR}/avoindata/config/install

# reload custom modules
# NOTE: ansible role skips errors with this condition:
#       result.rc == 1 and 'The source directory does not exist. The source is not a directory.' not in result.stderr and 'already exists' not in result.stderr
echo "import module configurations.."
drush config:import -y --partial --source ${MOD_DIR}/avoindata-header/config/install           || true
drush config:import -y --partial --source ${MOD_DIR}/avoindata-footer/config/install           || true
drush config:import -y --partial --source ${MOD_DIR}/avoindata-articles/config/install         || true
drush config:import -y --partial --source ${MOD_DIR}/avoindata-events/config/install           || true
drush config:import -y --partial --source ${MOD_DIR}/avoindata-guide/config/install            || true

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
echo "import site config.."
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

# init users and roles
python3 ${SCRIPT_DIR}/init_users.py

# make sure file permissions are correct
chown -R www-data:www-data ${SITE_DIR}/default/sync
chown -R www-data:www-data ${SITE_DIR}/default/files

# set init flag to done
echo "$DRUPAL_IMAGE_TAG" > ${DATA_DIR}/.init-done
