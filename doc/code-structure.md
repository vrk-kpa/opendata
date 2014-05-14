# Code structure

## CKAN

[CKAN](http://ckan.org/) is used in the project to provide dataset search features. We have forked CKAN to hotfix some bugs in the core. As CKAN updates, these patches should be reviewed whether they have become obsolete. All new features are implemented as [extensions](http://docs.ckan.org/en/latest/extensions/index.html). Some of the extensions in use are developed in-house, some are forked and patched and some are used out-of-the-box.

Logic code in CKAN is separated into several categories (action, auth, controller, logic).

HTML layout is specified as [Jinja templates](http://docs.ckan.org/en/latest/theming/index.html). Templates can introduce named blocks, which extensions can then overwrite while inheriting the rest of the blocks from the template. If changes outside a named block are necessary (e.g. reordering blocks, blockless template code etc.), the whole template file must be copied. This leads to a lot of code being copied in vain from core CKAN. As the copy overrides future CKAN updates, this should be avoided.


## Drupal

[Drupal](http://drupal.org/) is used to provide content management features. All new features are implemented as [modules](https://drupal.org/developing/modules). A few of the less tedious and seldom tasks have not been worth automating, must most functionality has been automated with Ansible. Drupal's CLI [Drush](https://github.com/drush-ops/drush) is used extensively via Ansible to automate the site setup.

The HTML layout is provided as a custom theme module that inherits the [Drupal Bootstrap theme](https://drupal.org/project/bootstrap). Some aesthetic functions have been implemented in the theme, but in general, embedding functionality into the theme should be avoided, and provided as separate modules instead.


## Ansible playbooks

The _ansible_ directory contains [Ansible playbooks](http://docs.ansible.com/playbooks.html) that describe series of tasks that Ansible should run to install a reproducible copy of the service. Tasks are split into roles which can all be installed on one machine (single-machine.yml), or split into a cluster of machines (cluster.yml).


## Vagrantfile

The _vagrant_ directory includes configuration needed to setup a virtual machine and customize Ansible in order to create a local copy of the service for developers. The most important file here is the [Vagrantfile](https://docs.vagrantup.com/v2/vagrantfile/).
