#!/bin/sh
set -e

echo "init_modules() ..."

# cleanup
rm -rf /opt/drupal/web/modules/avoindata-header
rm -rf /opt/drupal/web/modules/avoindata-servicemessage
rm -rf /opt/drupal/web/modules/avoindata-hero
rm -rf /opt/drupal/web/modules/avoindata-categories
rm -rf /opt/drupal/web/modules/avoindata-infobox
rm -rf /opt/drupal/web/modules/avoindata-datasetlist
rm -rf /opt/drupal/web/modules/avoindata-newsfeed
rm -rf /opt/drupal/web/modules/avoindata-appfeed
rm -rf /opt/drupal/web/modules/avoindata-footer
rm -rf /opt/drupal/web/modules/avoindata-articles
rm -rf /opt/drupal/web/modules/avoindata-events
rm -rf /opt/drupal/web/modules/avoindata-guide
rm -rf /opt/drupal/web/modules/avoindata-user
rm -rf /opt/drupal/web/modules/avoindata-ckeditor-plugins
rm -rf /opt/drupal/web/themes/avoindata

# install
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-header/.            /opt/drupal/web/modules/avoindata-header
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-servicemessage/.    /opt/drupal/web/modules/avoindata-servicemessage
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-hero/.              /opt/drupal/web/modules/avoindata-hero
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-categories/.        /opt/drupal/web/modules/avoindata-categories
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-infobox/.           /opt/drupal/web/modules/avoindata-infobox
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-datasetlist/.       /opt/drupal/web/modules/avoindata-datasetlist
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-newsfeed/.          /opt/drupal/web/modules/avoindata-newsfeed
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-appfeed/.           /opt/drupal/web/modules/avoindata-appfeed
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-footer/.            /opt/drupal/web/modules/avoindata-footer
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-articles/.          /opt/drupal/web/modules/avoindata-articles
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-events/.            /opt/drupal/web/modules/avoindata-events
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-guide/.             /opt/drupal/web/modules/avoindata-guide
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-user/.              /opt/drupal/web/modules/avoindata-user
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-ckeditor-plugins/.  /opt/drupal/web/modules/avoindata-ckeditor-plugins
/bin/cp -rf ${MOD_DIR}/avoindata-drupal-theme/.             /opt/drupal/web/themes/avoindata

/bin/cp -rf ${RES_DIR}/vendor/@fortawesome/fontawesome/webfonts/.  /opt/drupal/web/themes/avoindata/fonts
/bin/cp -rf ${RES_DIR}/vendor/bootstrap/dist/fonts/.               /opt/drupal/web/themes/avoindata/fonts
