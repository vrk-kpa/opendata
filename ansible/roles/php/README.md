Ansible php role
=========

This role installs PHP and PHP-FPM service.

Requirements
------------

None

Role Variables
--------------

#### `php_www_user` (optional)
User account name for PHP-FPM service, default value: `www-data`

#### `php_www_group` (optional)
User account group name for PHP-FPM service, default value: `www-data`

#### `php_packages_state` (optional)
Defines if php package state, default value: `present`. Set to latest for updating
php packages.

#### `php_fpm_service` (optional)
Name of the PJP-FPM service, default value: `php7.0-fpm.service`

#### `php_fpm_config_file` (optional)
Path to PHP-FPM service configuration file, default value: `/etc/php/7.0/fpm/pool.d/www.conf`

#### `php_required_packages` (optional)
List of required packages for this role.

Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: php, tags: php }

License
-------

MIT
