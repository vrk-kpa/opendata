#! /bin/sh

# CKAN installation script
# Not fully tested.
# By default installs to home folder: use config.sh to modify values
# Requires Ubuntu 12.04 (13.04 fails) using package. 
# http://docs.ckan.org/en/latest/installing.html

FROM_SOURCE=false
UPGRADE_PACKAGES=false
DATABASE_PASSWORD="pass"
DATE=`date --iso-8601=seconds`
BACKUP_DIRECTORY=/etc/solr/conf/backup
WORK_DIRECTORY="/tmp"
CKAN_PACKAGE="python-ckan_2.1_amd64.deb"
SOURCE_DIRECTORY="$HOME/ckan"
VIRTUAL_ENVIRONMENT="/usr/lib/ckan/default"
CKAN_INI=""

if [ -f "/etc/ytp/config" ]; then
	. /etc/ytp/config
fi

if [ "$CKAN_INI" = "" ]; then
	if $FROM_SOURCE; then
		CKAN_INI="/etc/ckan/default/development.ini"
	else
		CKAN_INI="/etc/ckan/default/production.ini"
	fi
fi

if [ "$DATABASE_PASSWORD" = "" ]; then
	echo "DATABASE_PASSWORD must be set"
	exit 1
fi

if $UPGRADE_PACKAGES; then
	sudo apt-get -y update
	sudo apt-get -y upgrade
fi

# install requirements
sudo apt-get -y install nginx apache2 libapache2-mod-wsgi libpq5 postgresql solr-jetty openjdk-7-jdk

# Source install does not include Apache and Nginx configuration
# Source install should be done only on development machine
if $FROM_SOURCE; then
	sudo apt-get -y install python-dev postgresql libpq-dev python-pip python-virtualenv git-core solr-jetty

	mkdir -p $SOURCE_DIRECTORY/lib
	mkdir -p $SOURCE_DIRECTORY/etc

	sudo ln -sf $SOURCE_DIRECTORY/lib /usr/lib/ckan
	sudo ln -sf $SOURCE_DIRECTORY/etc /etc/ckan

	mkdir -p $VIRTUAL_ENVIRONMENT
	# sudo chown `whoami` /usr/lib/ckan/default
	virtualenv --no-site-packages $VIRTUAL_ENVIRONMENT
	. $VIRTUAL_ENVIRONMENT/bin/activate
	echo "Installing from source: might take some time to download from git"
	pip install -e 'git+https://github.com/okfn/ckan.git@ckan-2.1#egg=ckan'
	pip install -r $VIRTUAL_ENVIRONMENT/src/ckan/requirements.txt

	mkdir -p /etc/ckan/default
	cd /usr/lib/ckan/default/src/ckan
	paster make-config --no-interactive ckan $CKAN_INI

	deactivate

	ln -sf /usr/lib/ckan/default/src/ckan/who.ini /etc/ckan/default/who.ini

else
	if [ ! -f $WORK_DIRECTORY/$CKAN_PACKAGE ]; then
		wget http://packaging.ckan.org/$CKAN_PACKAGE --directory-prefix=$WORK_DIRECTORY
	fi

	sudo dpkg -i $WORK_DIRECTORY/$CKAN_PACKAGE
fi

# Configure Solr (and Jetty)
sudo sh -c 'echo "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nVERBOSE=yes" > /etc/default/jetty'
sudo sh -c 'echo "JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64" >> /etc/default/jetty'

sudo mkdir -p $BACKUP_DIRECTORY
sudo mv /etc/solr/conf/schema.xml $BACKUP_DIRECTORY/schema.xml.bak-$DATE
sudo ln -sf /usr/lib/ckan/default/src/ckan/ckan/config/solr/schema-2.0.xml /etc/solr/conf/schema.xml

sudo service jetty restart

# Initialize postgres database
if [ ! `sudo -u postgres psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='ckan_default'"`  ]; then
	sudo -u postgres createuser -E -S -D -R ckan_default
fi

sudo -u postgres psql -U postgres -d postgres -c "alter user ckan_default with password '$DATABASE_PASSWORD';"

if [ ! `sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='ckan_default'"` ]; then
	sudo -u postgres createdb -O ckan_default ckan_default -E utf-8
fi

sudo sed -i "s/^sqlalchemy.url.*/sqlalchemy.url = postgres:\/\/ckan_default:$DATABASE_PASSWORD@localhost\/ckan_default/" $CKAN_INI
sudo sed -i "s/^ckan.locale_default.*/ckan.locale_default = fi/" $CKAN_INI
sudo sed -i "s/^ckan.locales_offered.*/ckan.locales_offered = fi sv en/" $CKAN_INI

# Initialize tables
if $FROM_SOURCE; then
	. /usr/lib/ckan/default/bin/activate
	cd /usr/lib/ckan/default/src/ckan
	paster db init -c $CKAN_INI
	deactivate
else
	sudo ckan db init
	sudo service apache2 restart
	sudo service nginx restart
fi

