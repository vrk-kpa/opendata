Ansible role postgres
=========

This role is used for setting up postgresql server. It supports both local
installation or configuring AWS RDS postgres instance.

Requirements
------------

None

Role Variables
--------------



Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: postgres }

License
-------

MIT
