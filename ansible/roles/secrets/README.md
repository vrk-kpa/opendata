Ansible role secrets
=========

Used to include secrets variables from a file.

Requirements
------------

None

Role Variables
--------------


#### `secrets_file_path` (required)
Path to secrets file.

Dependencies
------------

None

Example Playbook
----------------


    - hosts: servers
      roles:
         - { role: secrets, secrets_file_path: "/my/sectets/path.yml"}

License
-------

MIT
