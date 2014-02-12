Yhteentoimivuuspalvelut (YTP)
=============================

Main project for Yhteentoimivuuspalvelut.

- Build (Ansible)
- Development (Vagrant)
- CI (Travis) [![Build Status][travis-image]][travis-url]

## Local installation

### Requirements

- Ubuntu x86_64 (tested with 13.04 and 13.10)


### Source

Fetch source codes

    git clone https://github.com/yhteentoimivuuspalvelut/ytp.git
    cd ytp
    git submodule init
    git submodule update 

Note that if submodules are updated, you need to `init` and `update` those after `pull`.


### Ansible

Ansible 1.4+ is required

    sudo add-apt-repository ppa:rquillo/ansible
    sudo apt-get update
    sudo apt-get install ansible
    sudo apt-get install python-keyczar


### Vagrant

Vagrant is used to test and develop the service.


#### Install Virtualbox

    sudo apt-get install virtualbox

**Alternatively** install from Oracle Debian repository [https://www.virtualbox.org/wiki/Linux_Downloads](https://www.virtualbox.org/wiki/Linux_Downloads)

    # Add one of the following lines according to your distribution to your /etc/apt/sources.list:
    # deb http://download.virtualbox.org/virtualbox/debian saucy contrib
    wget -q http://download.virtualbox.org/virtualbox/debian/oracle_vbox.asc -O- | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install virtualbox-4.3


#### Install Vagrant from package

Download Vagrant latest 64-bit version for Ubuntu from [http://www.vagrantup.com/downloads.html](http://www.vagrantup.com/downloads.html)

    sudo dpkg -i vagrant_1.4.3_x86_64.deb


#### Run Vagrant and start Ansible installation

    cd ytp/vagrant
    vagrant up

Re-run provision, if Ansible fails to ssh. 

    vagrant provision

To re-run process use `provision`. If you remove the virtual machine (`vagrant destroy`) you need to use `up` again.


#### Access to service

Access to service at [http://10.10.10.10/](http://10.10.10.10/) when installation is ready.


#### Notes

- Access to virtual machine via ssh use: `vagrant ssh`
- The modules are mapped to `/src` path on virtual machine
- Use `vagrant halt` when you are done working on virtual machine and `vagrant destroy` to remove virtual machine.
- Ansible and Vagrant options are at `Vagrantfile`


### Development in Vagrant

You can develop in full installation by replacing the sources in the virtualbox. Then you can edit the files on local machine because the /src/ is mapped to ../modules

Look at individual instructions for each project at Github project page.

#### Automatic project switch

The ytp-develop.py -script is created to automated project switching on Vagrant.

    /src/ytp-tools/scripts/ytp-develop.py # help
    /src/ytp-tools/scripts/ytp-develop.py --list # list available projects
    /src/ytp-tools/scripts/ytp-develop.py --serve # serve CKAN via paster and access at http://10.10.10.10:5000/
    /src/ytp-tools/scripts/ytp-develop.py <project-name> # switch project sources

Example: /src/ytp-tools/scripts/ytp-develop.py ckanext-ytp-dataset

Notes.
- Serve command cannot reload all modification and need to restarted on some changes.
- For ckanext project if setup.py is changed or if some files are inserted you need to re-execute ytp-develop.py

#### Manually switch Python packages (ckanext-*)

    vagrant ssh
    cd /src/<python-package>
    sudo /usr/lib/ckan/default/bin/pip uninstall <python-package>
    sudo /usr/lib/ckan/default/bin/python setup.py develop

- You must restart Apache after modifications to sources *sudo service apache2 restart*. 
- If you modify *setup.py* re-run *setup.py develop*. 


##### Manually switch running CKAN via PasteScript

As modifications to Python packages require Apace restart, you can use *paster* for development. 

    vagrant ssh
    sudo ufw allow 5000
    . /usr/lib/ckan/default/bin/activate # or /usr/lib/ckan/default/bin/paster ...
    paster serve /etc/ckan/default/production.ini

Now you can access CKAN at [http://10.10.10.10:5000/](http://10.10.10.10:5000/)


#### Manually switch Drupal theme (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/ytp/sites/all/themes
    sudo mv ytp_theme /var/www/backup_ytp_theme
    sudo ln -s /src/ytp-theme-drupal ytp_theme


#### Manually switch Assets (ytp-theme-drupal)

    vagrant ssh
    cd /var/www/
    sudo mv resources /var/www/backup_resources
    sudo ln -s /src/ytp-assets-common/resources/ resources


## Known issues

Sometimes the Accelerate in Ansible breaks the SSH connection.  

    "GATHERING FACTS: fatal: [10.10.10.10] => SSH encountered an unknown error during the connection. We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue"
    or
    "fatal: [10.10.10.10] => decryption failed"

Kill acceleration process on machine and re-run the provision 

    vagrant ssh
    ps aux | grep acceleration
    kill <acceleration-pid>
    exit
    vagrant provision # re-run


## Contact

Please file [issues at Github](https://github.com/yhteentoimivuuspalvelut/ytp/issues) or join the discussion at [avoindata.net](http://avoindata.net/)


## Copying and License

This material is copyright (c) 2013 Valtiokonttori / Finnish State Treasury.

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at: http://www.fsf.org/licensing/licenses/agpl-3.0.html

[travis-url]: https://travis-ci.org/yhteentoimivuuspalvelut/ytp
[travis-image]: https://travis-ci.org/yhteentoimivuuspalvelut/ytp.png?branch=master
