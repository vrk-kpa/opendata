Ansible role mailhog
=========

This ansible role installs MailHog email testing tool for developers.

Requirements
------------
None

Role Variables
--------------

* **mailhog_install_dir**: Install directory for MailHog
* **mailhog_version**: MailHog version
* **mailhog_release_url**: URL where MailHog binary is downloaded from
* **mailhog_mhsendmail_version**: MailHog sendmail version
* **mailhog_mhsendmail_release_url**: URL where MailHog sendmail (mhsendmail) binary is downloaded from

Dependencies
------------
None

Example Playbook
----------------

    - hosts: servers
      roles:
         - mailhog

License
-------

MIT
