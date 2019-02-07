Ansible role composer
=========

Installs Composer Dependency Manager for PHP

Requirements
------------
None

Role Variables
--------------

#### `composer_path` (optional)
Path for composer executable, default value: `/usr/local/bin/composer`.

#### `composer_home_path` (optional)
Path for composer home directory, default value: `~/.composer`.

#### `composer_home_owner` (optional)
Owner of composer home, default value: `www-data`

#### `composer_home_group` (optional)
Group of composer home, default value: `www-data`

Dependencies
------------
None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: composer, tags: composer }

License
-------

MIT
