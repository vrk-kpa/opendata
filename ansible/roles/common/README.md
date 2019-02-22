Ansible role common
=========

A role for generic tasks that do not fit into specific roles .

Requirements
------------

Role Variables
--------------
#### `common_deployment_environment_id` (required)
Id of the environment

Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: common, common_deployment_environment_id: vagrant }

License
-------

MIT
