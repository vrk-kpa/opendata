Ansible role datapusher
=========

Ansible role for instaling Datapusher (https://github.com/6aika/datapusher).

Requirements
------------

None

Role Variables
--------------
#### `datapusher_deployment_environment_id` (required)
Environment id for datapusher

#### `datapusher_env` (optional)
Path for datapusher virtual env, default: /usr/lib/ckan/datapusher

#### `datapusher_group` (optional)
Group for datapusher files, default: www-data

#### `datapusher_user` (optional)
Owner for datapusher files, default: www-data

Dependencies
------------

Apache role with proper site and port configuration.

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: datapusher, datapusher_deployment_environment_id: prod }

License
-------

MIT
