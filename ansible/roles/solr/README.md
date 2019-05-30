Ansible solr role
=========

This role installs solr 6 with CKAN specific schema

Requirements
------------

None

Role Variables
--------------
#### `solr_host` (optional)
Solr host

#### `solr_port` (optional)
Default value is 8983

#### `solr_cores` (optional)
List of cores

#### `solr_version` (optional)
Solr version used (default is 6.5.1)

#### `solr_download_url` (optional)
Url for Solr package

#### `solr_user` (optional)
Solr user (default is solr)

#### `solr_group` (optional)
Solr group (default is solr)

#### `solr_requirements` (optional)
List of required packages for running Solr.

#### `solr_install_path` (optional)
Destination path for Solr installation.

#### `solr_config_file` (optional)
Solr configuration file path.

#### `solr_service_name` (optional)
Name of the service.

#### `solr_service_state` (optional)
State of Solr service.

#### `solr_service_enabled` (optional)
Defines if the Solr service is enabled.

#### `solr_core_config_files` (optional)
List of templated configuration files that are copied for each core.

Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: solr }

License
-------

MIT
