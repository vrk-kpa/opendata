## Ansible roles and playbooks

Ansible directory contains inventory, roles and playbooks used by the project. Ansible is used for different purposes in this project. Some of the playbooks are used for testing and development phases, some for building AMIs and some for configuring virtual machine during bootstrap phase.

### Development environment playbook

[single-server.yml](./single-server.yml) is a playbook that is used by [Vagrantfile](../Vagrantfile) for creating a local development environment. It contains all the same roles as the one used for production plus some additional roles like mailhog for mocking mail service.

### Playbooks for deploying Cloudformation stacks

[opendata_cloudfront.yml](./opendata_cloudfront.yml) playbook can be used for creating stack using [cloudfront.yml](../cloudformation/cloudfront.yml)

Respectively [opendata_webstack.yml](./opendata_web_stack.yml) playbook can be used for deploying [instances.yml](../cloudformation/instances.yml) stack.

Other templates currently do not have playbooks for deploying using Ansible. When running the playbook you need to have AWS credentials configured properly. You can use tool like aws-vault for providing the credentials, for example:

```
aws-vault exec <profile> -- ansible-playbook -i inventories/beta opendata_web_stack.yml
```

### Playbooks used in CI/CD and in launch templates

[circleci_build_test.yml](./circleci_build_test.yml) and [circleci_cleanup.yml](./circleci_cleanup.yml) are used as part of CI/CD pipeline. The former is used for creating an EC2 instance, deploying application and running the tests against it and the latter is for cleaning up test EC2 instances.

[web-server.yml](./web-server.yml) and [scheduled-server.yml](./scheduled-server.yml) playbooks are used both for creating AMIs by Packer ([packer/packer-web.json](../packer/packer-web.json) and [packer/packer-scheduled.json](../packer/packer-scheduled.json)) and when bootstrapping EC2 instances. When these playbooks are used by Packer tasks tagged using "configure" are skipped. These tasks are then executed when the EC2 instances are started (see [cloudformation/launchtemplate.yml](../cloudformation/launchtemplate.yml)).

