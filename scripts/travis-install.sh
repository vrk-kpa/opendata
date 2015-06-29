#! /bin/sh -e

# CKAN install script for Travis CI 

DATABASE_PASSWORD="pass"
DATE=`date --iso-8601=seconds`
SOURCE_DIRECTORY="$HOME/ckan"
VIRTUAL_ENVIRONMENT="/usr/lib/ckan/default"
TEST_INI="/usr/lib/ckan/default/src/ckan/test-core.ini"
SOURCE_DIRECTORY=`pwd`

# install requirements
sudo apt-get -qq -y update
sudo apt-get -qq -y install python-virtualenv solr-jetty 

sudo service postgresql reload

pip install flake8 --download-cache=$HOME/cache

mkdir -p $SOURCE_DIRECTORY/lib
mkdir -p $SOURCE_DIRECTORY/etc

sudo ln -sf $SOURCE_DIRECTORY/lib /usr/lib/ckan
sudo ln -sf $SOURCE_DIRECTORY/etc /etc/ckan

mkdir -p $VIRTUAL_ENVIRONMENT
virtualenv --no-site-packages $VIRTUAL_ENVIRONMENT
. $VIRTUAL_ENVIRONMENT/bin/activate

export PIP_USE_MIRRORS=true
pip install -e 'git+https://github.com/okfn/ckan.git@ckan-2.3#egg=ckan'
pip install --use-mirrors -r $VIRTUAL_ENVIRONMENT/src/ckan/requirements.txt --download-cache=$HOME/cache
pip install --use-mirrors -r test_requirements.txt --download-cache=$HOME/cache

for plugin in modules/*; do
    if [ -f $plugin/requirements.txt ]; then
        echo "Installing requirements for $plugin"
        cd $plugin
        pip install --use-mirrors -r requirements.txt --download-cache=$HOME/cache
        cd $SOURCE_DIRECTORY
    fi
done

mkdir -p /etc/ckan/default

# Configure Solr (and Jetty)
sudo sh -c 'echo "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nVERBOSE=yes\nJAVA_HOME=$JAVA_HOME" > /etc/default/jetty'

sudo cp /usr/lib/ckan/default/src/ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml

sudo service jetty restart

# Initialize postgres database
for username in ckan_default ckan_test; do
    if [ ! `sudo -u postgres psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$username'"`  ]; then
        sudo -u postgres psql -c "CREATE USER $username WITH PASSWORD '$DATABASE_PASSWORD';"    
    fi
    sudo -u postgres psql -U postgres -d postgres -c "ALTER USER $username WITH PASSWORD '$DATABASE_PASSWORD';"
done

for database in ckan_test; do
    if [ `sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$database'"` ]; then
        sudo -u postgres psql -c "DROP DATABASE $database;"
    fi
    sudo -u postgres psql -c "CREATE DATABASE $database WITH OWNER ckan_default;"
done

cd /usr/lib/ckan/default/src/ckan/
paster db init -c $TEST_INI
cd $SOURCE_DIRECTORY
