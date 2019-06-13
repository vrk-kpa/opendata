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


#### `dynatrace_app_log_content_access` (optional)
Sets log access to either enabled or disabled based on the state of this (0/1), default 1


#### `dynatrace_install_oneagent` (optional)
Boolean value for (un)installation of Dynatrace OneAgent, default true.


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
