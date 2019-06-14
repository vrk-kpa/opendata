Ansible role secrets
=========

Used to copy files from S3 and include secrets variables from a file.

Requirements
------------

None

Role Variables
--------------


#### `secrets_bucket` (required)
AWS S3 bucket for secrets.

#### `secrets_bucket_files` (required)
List of files that are copied from S3.

#### `secrets_bucket_path` (optional)
Path for secret files in S3 bucket.

#### `secrets_destination_path` (required)
Destination path for secret files.

#### `secrets_file` (required)
Name of the file where secret ansible variables are included

Dependencies
------------

None

Example Playbook
----------------


    - hosts: servers
      roles:
         - { role: secrets }

License
-------

MIT
