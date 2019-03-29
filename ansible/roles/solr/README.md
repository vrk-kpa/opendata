Ansible solr role
=========

This role installs solr (jetty).

Requirements
------------

None

Role Variables
--------------
#### `solr_jetty_service` (optional)
Name of the jetty service

#### `solr_port` (optional)
Default value is 8983

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
