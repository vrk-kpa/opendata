
# Development in Vagrant

You can develop in full installation by replacing the sources in the virtualbox. Then you can edit the files on local machine because the /src/ is mapped to ../modules

Look at individual instructions for each project at Github project page.

## Automatic project switch

The ytp-develop.py -script is created to automated project switching on Vagrant. This script is executed under Vargant (`vagrant ssh`).

    sudo /src/ytp-tools/scripts/ytp-develop.py # help
    sudo /src/ytp-tools/scripts/ytp-develop.py --list # list available projects
    sudo /src/ytp-tools/scripts/ytp-develop.py --serve # serve CKAN via paster and access at http://10.10.10.10:5000/
    sudo /src/ytp-tools/scripts/ytp-develop.py <project-name>... # switch project sources

Examples:

    sudo /src/ytp-tools/scripts/ytp-develop.py ckanext-ytp-dataset # replace ckanext-ytp-dataset project
    sudo /src/ytp-tools/scripts/ytp-develop.py ckanext-ytp-theme ytp-assets-common # replace both ckanext-ytp-theme and ytp-assets-common projects 

### Notes

- Serve command cannot reload all modification and need to restarted on some changes.
- Serve cannot access asset files currently so layout is broken. You can disable ytp_theme plugin from `/etc/ckan/default/production.ini`. 
- For ckanext project if setup.py is changed or if some files are inserted you need to re-execute `ytp-develop.py` (executes correct python setup.py develop).

## Manually switch Python packages (ckanext-*)

    vagrant ssh
    cd /src/<python-package>
    sudo /usr/lib/ckan/default/bin/pip uninstall <python-package>
    sudo /usr/lib/ckan/default/bin/python setup.py develop

- You must restart Apache after modifications to sources *sudo service apache2 restart*. 
- If you modify *setup.py* re-run *setup.py develop*. 


### Manually switch running CKAN via PasteScript

As modifications to Python packages require Apace restart, you can use *paster* for development. 

    vagrant ssh
    sudo ufw allow 5000
    . /usr/lib/ckan/default/bin/activate # or /usr/lib/ckan/default/bin/paster ...
    paster serve /etc/ckan/default/production.ini

Now you can access CKAN at [http://10.10.10.10:5000/](http://10.10.10.10:5000/)


## Manually switch Drupal theme (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/ytp/sites/all/themes
    sudo mv ytp_theme /var/www/backup_ytp_theme
    sudo ln -s /src/ytp-theme-drupal ytp_theme


## Manually switch Assets (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/
    sudo mv resources /var/www/backup_resources
    sudo ln -s /src/ytp-assets-common/resources/ resources


## Manually running ckanext tests

    . /usr/lib/ckan/default/bin/activate
    cd modules/ckanext-ytp-<name>
    nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --with-coverage --cover-package ckanext.ytp
    # or
    nosetests --ckan --with-pylons=test.ini `find -iname tests -type d` --nocapture
