# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# This Vagrantfile sets up a virtual machine and installs the YTP service
# on it to create a local development environment.
#
# Tested with Vagrant 1.6.1 and VirtualBox 4.3.10 on Ubuntu 14.04 64-bit

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "ytp" do |ytp|
    ytp.vm.box = "bento/ubuntu-16.04"

    ytp.vm.network :private_network, ip: "10.10.10.10"

    # Sync source code directories from host to guest
    case RUBY_PLATFORM
    when /mswin|msys|mingw|cygwin|bccwin|wince|emc/
        # Fix Windows file rights, otherwise Ansible tries to execute files
        ytp.vm.synced_folder ".", "/vagrant", type:"virtualbox", :mount_options => ["dmode=755","fmode=644"]
    end

    ytp.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "ansible/single-server.yml"
      ansible.verbose = "v"
      ansible.inventory_path = "vagrant/vagrant-ansible-inventory"
      ansible.skip_tags = "non-local,postfix"
      ansible.limit = 'all'
      # ansible.extra_vars = { clear_module_cache: true }
      # ansible.tags = "modules,ckan,drupal"
      # ansible.start_at_task = ""
    end

    ytp.vm.provider "virtualbox" do |vbox|
      vbox.memory = 1536
    end
  end

  # http://docs.vagrantup.com/v2/multi-machine/index.html
  #config.vm.define "db" do |db|
end
