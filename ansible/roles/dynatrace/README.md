Ansible role Dynatrace
=========

Ansible role for installing Dynatrace OneAgent

Requirements
------------

None

Role Variables
--------------


#### `dynatrace_oneagent_installer_script_url` (required)
Url for dynatrace installer


#### `secrets_file_path` (optional)
Sets log access to either enabled or disabled based on the state of this (0/1), default 0


#### `dynatrace_install_oneagent` (required)
Boolean value for (un)installation of OnAgent


Dependencies
------------

secrets role

Example Playbook
----------------


    - hosts: servers
      roles:
         - { role: dynatrace, dynatrace_oneagent_installer_script_url: "https://XXXXXXXXXXXXXXX.dynatrace.com/api/v1/deployment/installer/agent/unix/default/latest?Api-Token=YYYYYYYYYYYYYYYY&flavor=default" }

License
-------

MIT
