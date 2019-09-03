# Local installation

## Requirements

- Virtualbox (tested with 6.0)
- Vagrant (tested with 2.2.4)

## Source

Fetch source codes

    git clone https://github.com/vrk-kpa/opendata.git
    cd opendata
    
Fetch submodules

    git submodule update --init --recursive

### Run Vagrant and start Ansible installation

Vagrant command uses the Vagrantfile which contains all the virtual machine configurations, therefore you should run the command in the project directory or its subdirectories.

`vagrant up` will both start and then provision your virtual machine. If the machine is already running, this command does nothing. To only start a machine but not provision it, you can use `vagrant up --no-provision`. By default, Vagrant will not reprovision a halted machine that has already been provisioned earlier, but if you wish to start up a completely new machine without provisioning it, you can use the previous command.

`vagrant ssh` connects to the virtual machine over SSH as vagrant user. You can also use conventional ssh command, but this way you do not need to hassle with username, key, IP address and port.

`vagrant provision` will reprovision a running machine.

`vagrant halt` will shutdown a running machine, use `vagrant up` to boot it up again.

`vagrant destroy` will completely remove the virtual machine, requiring you to create a new one with `up` again.

### Advanced provisioning with Ansible

If you need to make adjustments to the provisioning configuration, you can either edit the Ansible settings in the Vagrant file, or simply run Ansible without Vagrant:

    # cd into the main ytp directory (cd /vagrant inside vagrant)
    ansible-playbook --inventory-file=ansible/inventories/vagrant -v ansible/single-server.yml

### Access to service

After the provisioning of the server is ready, access the service at [http://vagrant.avoindata.fi/](http://vagrant.avoindata.fi/). Environment for integration tests is available at [http://vagrant.avoindata.fi:9000/](http://vagrant.avoindata.fi:9000/).
