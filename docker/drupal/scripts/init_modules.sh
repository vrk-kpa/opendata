#!/bin/sh
set -e

echo "init_modules() ..."

if [ ! -f /opt/modules/.init-done ]; then
  echo "waiting for custom modules to be ready..."
  sleep 1s
  exit 1
else
  echo "initializing custom module links..."
  ln -snf /opt/modules/avoindata-drupal-header            /opt/drupal/web/modules/avoindata-header
  ln -snf /opt/modules/avoindata-drupal-servicemessage    /opt/drupal/web/modules/avoindata-servicemessage
  ln -snf /opt/modules/avoindata-drupal-hero              /opt/drupal/web/modules/avoindata-hero
  ln -snf /opt/modules/avoindata-drupal-categories        /opt/drupal/web/modules/avoindata-categories
  ln -snf /opt/modules/avoindata-drupal-infobox           /opt/drupal/web/modules/avoindata-infobox
  ln -snf /opt/modules/avoindata-drupal-datasetlist       /opt/drupal/web/modules/avoindata-datasetlist
  ln -snf /opt/modules/avoindata-drupal-newsfeed          /opt/drupal/web/modules/avoindata-newsfeed
  ln -snf /opt/modules/avoindata-drupal-appfeed           /opt/drupal/web/modules/avoindata-appfeed
  ln -snf /opt/modules/avoindata-drupal-footer            /opt/drupal/web/modules/avoindata-footer
  ln -snf /opt/modules/avoindata-drupal-articles          /opt/drupal/web/modules/avoindata-articles
  ln -snf /opt/modules/avoindata-drupal-events            /opt/drupal/web/modules/avoindata-events
  ln -snf /opt/modules/avoindata-drupal-guide             /opt/drupal/web/modules/avoindata-guide
  ln -snf /opt/modules/avoindata-drupal-user              /opt/drupal/web/modules/avoindata-user
  ln -snf /opt/modules/avoindata-drupal-ckeditor-plugins  /opt/drupal/web/modules/avoindata-ckeditor-plugins
  ln -snf /opt/modules/avoindata-drupal-theme             /opt/drupal/web/themes/avoindata
  echo "copying custom module fonts..."
  /bin/cp -rf /opt/modules/ytp-assets-common/resources/vendor/@fortawesome/fontawesome/webfonts/.  /opt/drupal/web/themes/avoindata/fonts
  /bin/cp -rf /opt/modules/ytp-assets-common/resources/vendor/bootstrap/dist/fonts/.               /opt/drupal/web/themes/avoindata/fonts
fi
