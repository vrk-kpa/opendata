echo "Upgrade CKAN database ..."
ckan -c ${APP_DIR}/ckan.ini db upgrade


echo "Initialize CKAN extension databases ..."
ENABLED_CKAN_PLUGINS=$(grep "^ckan.plugins =" ${APP_DIR}/ckan.ini | sed 's/^ckan.plugins =//')

ckanext_db_upgrade() {
  echo "Upgrading CKAN extension database for $1"
  if [[ "${ENABLED_CKAN_PLUGINS}" == *" $1 "* ]]; then
    ckan -c ${APP_DIR}/ckan.ini db upgrade -p "$1";
  else
    echo "CKAN extension $1 is not enabled, skipping database upgrade..."
  fi
}

ckanext_db_upgrade ckanext-ytp_spatial
ckanext_db_upgrade ckanext-ytp_reminder
ckanext_db_upgrade apis
ckanext_db_upgrade harvest
ckanext_db_upgrade sixodp-showcase  # contains showcase migrations
ckanext_db_upgrade qa
ckanext_db_upgrade matomo
ckanext_db_upgrade report
ckanext_db_upgrade archiver
ckanext_db_upgrade cloudstorage
ckanext_db_upgrade reminder
