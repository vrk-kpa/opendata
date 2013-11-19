#! /bin/sh

DRUPAL_NAME="ytp"
SITE_NAME="YTP"
WWW_ROOT="/var/www"
DRUPAL_ROOT="$WWW_ROOT/$DRUPAL_NAME"

WWW_USER="www-data"
WWW_GROUP=$WWW_USER

DRUPAL_DATABASE="drupal"
DRUPAL_DATABASE_PASSWORD="drupal"
DRUPAL_DATABASE_USERNAME="drupal"

ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin"

DATE=`date --iso-8601=seconds`
BACKUP_DIRECTORY=$WWW_ROOT

if [ -f "/etc/ytp/config" ]; then
    . /etc/ytp/config
fi

sudo apt-get -y install php5-pgsql nginx php5-gd php5-fpm php-pear

# Drush version 5 or greater provides "drush make"
sudo pear channel-discover pear.drush.org
sudo pear install drush/drush

sudo sh -c "echo 'host $DRUPAL_DATABASE $DRUPAL_DATABASE_USERNAME 127.0.0.1/32 password' >> /etc/postgresql/9.1/main/pg_hba.conf"
sudo sh -c "echo 'localhost:5432:$DRUPAL_DATABASE:$DRUPAL_DATABASE_USERNAME:$DRUPAL_DATABASE_PASSWORD' > /root/.pgpass"
sudo chmod 600 /root/.pgpass
sudo service postgresql restart

if [ ! `sudo -u postgres psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DRUPAL_DATABASE_USERNAME'"` ]; then
	sudo -u postgres createuser -E -S -D -R $DRUPAL_DATABASE_USERNAME
fi

sudo -u postgres psql -U postgres -d postgres -c "ALTER USER $DRUPAL_DATABASE_USERNAME WITH PASSWORD '$DRUPAL_DATABASE_PASSWORD';"

sudo sed -i "s/^;?cgi.fix_pathinfo.*/cgi.fix_pathinfo=0/" /etc/php5/fpm/php.ini
sudo sed -i "s/^listen.*/listen=\/tmp\/phpfpm.socket/" /etc/php5/fpm/pool.d/www.conf

sudo rm -f /etc/nginx/sites-enabled/*
sudo cp $CONFIG_DIRECTORY/nginx.ytp.conf /etc/nginx/sites-available/ytp
sudo rm /etc/nginx/sites-enabled/*
sudo ln -sf ../sites-available/ytp /etc/nginx/sites-enabled/ytp

sudo service php5-fpm restart
sudo service nginx restart

if [ ! `sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DRUPAL_DATABASE'"` ]; then
	if [ -d $DRUPAL_ROOT ]; then
		BACKUP=$BACKUP_DIRECTORY/vk-drupal-backup-$DATE.tgz
		sudo tar czf $BACKUP $DRUPAL_ROOT
		sudo rm -R $DRUPAL_ROOT
		sudo chown 0:0 $BACKUP
		sudo chmod 600 $BACKUP
	fi
	sudo drush dl drupal --drupal-project-rename=$DRUPAL_NAME --destination=$WWW_ROOT --cache

	sudo mkdir -p $DRUPAL_ROOT/sites/default/files
	sudo chown $WWW_USER:$WWW_GROUP $DRUPAL_ROOT/sites/default/files

	sudo cp $DRUPAL_ROOT/sites/default/default.settings.php $DRUPAL_ROOT/sites/default/settings.php
	sudo chown $WWW_USER:$WWW_GROUP $DRUPAL_ROOT/sites/default/settings.php

	sudo -u postgres psql -U postgres -d postgres -c "ALTER USER $DRUPAL_DATABASE_USERNAME CREATEDB;"
	sudo -u postgres createdb -O $DRUPAL_DATABASE_USERNAME $DRUPAL_DATABASE -E utf-8
	cd $DRUPAL_ROOT
	yes | sudo drush site-install standard  --account-name=$ADMIN_USERNAME --account-pass=$ADMIN_PASSWORD \
		--db-url=pgsql://$DRUPAL_DATABASE_USERNAME:$DRUPAL_DATABASE_PASSWORD@localhost/$DRUPAL_DATABASE --site-name=$SITE_NAME
	cd $BASE_DIRECTORY
fi
sudo -u postgres psql -U postgres -d postgres -c "ALTER USER $DRUPAL_DATABASE_USERNAME NOCREATEDB;"

