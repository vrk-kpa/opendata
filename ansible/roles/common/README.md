Ansible role common
=========

A role for generic tasks that do not fit into specific roles .

Requirements
------------

Role Variables
--------------
#### `common_deployment_environment_id` (required)
Id of the environment

#### `common_users` (optional)

A dict describing user accounts to be added. For example:

```
common_users:
  - username: john
    state: present
    comment: "John Doe"
    groups:
      - somegroup
    publickeys:
      - 'ssh-rsa xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  - username: jane
    state: present
    comment: "Jane Doe"
    groups:
      - someothergroup
    publickeys:
      - 'ssh-rsa xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

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
