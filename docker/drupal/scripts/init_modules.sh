#!/bin/sh
set -e

echo "init_modules() ..."

# sync modules to final installation directory in parallel
echo "syncing modules..."
rsync -au --delete ${MOD_DIR}/avoindata-drupal-header/              /opt/drupal/web/modules/avoindata-header &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-servicemessage/      /opt/drupal/web/modules/avoindata-servicemessage &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-hero/                /opt/drupal/web/modules/avoindata-hero &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-categories/          /opt/drupal/web/modules/avoindata-categories &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-infobox/             /opt/drupal/web/modules/avoindata-infobox &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-datasetlist/         /opt/drupal/web/modules/avoindata-datasetlist &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-newsfeed/            /opt/drupal/web/modules/avoindata-newsfeed &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-appfeed/             /opt/drupal/web/modules/avoindata-appfeed &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-footer/              /opt/drupal/web/modules/avoindata-footer &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-articles/            /opt/drupal/web/modules/avoindata-articles &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-events/              /opt/drupal/web/modules/avoindata-events &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-guide/               /opt/drupal/web/modules/avoindata-guide &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-user/                /opt/drupal/web/modules/avoindata-user &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-ckeditor-plugins/    /opt/drupal/web/modules/avoindata-ckeditor-plugins &
rsync -au --delete ${MOD_DIR}/avoindata-drupal-theme/               /opt/drupal/web/themes/avoindata &
wait

# sync fonts to final installation directory in parallel
echo "syncing fonts..."
rsync -au ${RES_DIR}/vendor/@fortawesome/fontawesome/webfonts/      /opt/drupal/web/themes/avoindata/fonts &
rsync -au ${RES_DIR}/vendor/bootstrap/dist/fonts/                   /opt/drupal/web/themes/avoindata/fonts &
wait
