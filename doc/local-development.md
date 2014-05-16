
# Development in Vagrant

We have setup Vagrant so that you can have the source codes and IDE on your native host machine, while running a full installation of the service in VirtualBox. Live changes can be made to the server from the host machine, as the project subdirectory modules/ is mapped as /src/ inside the virtual machine. After provisioning the virtual machine, it uses the static codes installed on the server (which you can ofcourse temporarily edit by SSHing into the server). To live-edit code from the host machine, you must manually choose to symlink individual modules to have the server use the code from the host machine.

Look at individual instructions for each project at Github project page.

## Linking a module from the host machine

The ytp-develop.py script is provided to help with linking the modules. This script is executed on the virtual machine (`vagrant ssh`).

    sudo /src/ytp-tools/scripts/ytp-develop.py # help
    sudo /src/ytp-tools/scripts/ytp-develop.py --list # list available projects
    sudo /src/ytp-tools/scripts/ytp-develop.py --serve # serve CKAN via paster and access at http://10.10.10.10:5000/
    sudo /src/ytp-tools/scripts/ytp-develop.py <project-name>... # switch project sources

Examples:

    sudo /src/ytp-tools/scripts/ytp-develop.py ckanext-ytp-main # replace ckanext-ytp-main project
    sudo /src/ytp-tools/scripts/ytp-develop.py ckanext-ytp-main ytp-assets-common # replace both ckanext-ytp-main and ytp-assets-common projects 

### Notes

- Serve command cannot reload all modification and need to restarted on some changes.
- Serve cannot access asset files currently so the layout is broken. You can disable ytp_theme plugin from `/etc/ckan/default/production.ini`. 
- For ckanext project if setup.py is changed or if some files are inserted you need to re-execute `ytp-develop.py` (executes correct python setup.py develop).

## Manually link Python packages (ckanext-*)

    vagrant ssh
    cd /src/<python-package>
    sudo /usr/lib/ckan/default/bin/pip uninstall <python-package>
    sudo /usr/lib/ckan/default/bin/python setup.py develop

- You must restart Apache after modifications to sources *sudo service apache2 restart*. 
- If you modify *setup.py* re-run *setup.py develop*. 


### Manually running CKAN via PasteScript

As modifications to Python packages require Apace restart, you can use *paster* for development. 

    vagrant ssh
    sudo ufw allow 5000
    . /usr/lib/ckan/default/bin/activate # or /usr/lib/ckan/default/bin/paster ...
    paster serve /etc/ckan/default/production.ini

Now you can access CKAN at [http://10.10.10.10:5000/](http://10.10.10.10:5000/)


## Manually linking Drupal theme (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/ytp/sites/all/themes
    sudo mv ytp_theme /var/www/backup_ytp_theme
    sudo ln -s /src/ytp-theme-drupal ytp_theme


## Manually linking Assets (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/
    sudo mv resources /var/www/backup_resources
    sudo ln -s /src/ytp-assets-common/resources/ resources


## Manually running ckanext tests

    # create database once
    sudo -u postgres createdb -O ckan_default ckan_test

    . /usr/lib/ckan/default/bin/activate
    cd modules/ckanext-ytp-<name>
    nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
    # or
    nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --nocapture
