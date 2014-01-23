YTP - Yhteentoimivuuspalvelut
=============================

Main project for Yhteentoimivuuspalvelut.

- Build (Ansible)
- Development (Vagrant)
- CI (Travis)

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

To re-run process use `provision`. If you remove the machine (`vagrant destroy`) you need to use `up` again.


#### Access to service

Access to service at [http://10.10.10.10/](http://10.10.10.10/) when installation is ready.


#### Notes

- Access to machine via ssh use: `vagrant ssh`
- The modules are mapped to `/src` path on machine
- Use `vagrant halt` when you are done working on machine and `vagrant destroy` to remove machine.
- Ansible and Vagrant options are at `Vagrantfile`

### Development in Vagrant

You can develop in full installation by replacing the sources in machine. You can edit the files on local machine because the /src/ is mapped to ../modules

For python packages

    cd /src/<python-package>
    sudo pip uninstall <python-package>
    sudo python setup.py develop

For other packages you need to replace the directory on machine with link.

Drupal theme

    cd /var/www/ytp/sites/all/themes
    sudo mv ytp_theme /var/www/backup_ytp_theme
    sudo ln -s /src/ytp-theme-drupal ytp_theme

Assets

    cd /var/www/
    sudo mv shared /var/www/backup_shared
    sudo ln -s /src/ytp-assets-common/distribution/ shared

Look individual instructions for each project at Github project page.


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

Please file [issue at Github](https://github.com/yhteentoimivuuspalvelut/ytp/issues) or join to discussion at [avoindata.net](http://avoindata.net/)


## Copying and License

This material is copyright (c) 2013 Valtiokonttori / Finnish State Treasury.

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at:

http://www.fsf.org/licensing/licenses/agpl-3.0.html

