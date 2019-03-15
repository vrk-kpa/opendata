Ansible role drupal
=========

Ansible role for installing Drupal 8.

Requirements
------------
None

Role Variables
--------------

#### `drupal_name` (required)
Name of the drupal instance, default value: `drupal_name`.

#### `drupal_site_name` (required)
Drupal site name, default value: `drupal_site`

#### `drupal_user` (required)
User for drupal service, default value: www-user

#### `drupal_group` (required)
Group for drupal service, default value: www-user

#### `drupal_drush_path` (optional)
Path to drush binary, default

#### `drupal_custom_modules` (optional)
A list of drupal custom modules. For example

```
drupal_custom_modules:
  - { src_name: avoindata-drupal-header, module_name: avoindata-header, machine_name: avoindata_header }
  - { src_name: avoindata-drupal-hero, module_name: avoindata-hero, machine_name: avoindata_hero }
  - { src_name: avoindata-drupal-categories, module_name: avoindata-categories, machine_name: avoindata_categories }

```

#### `drupal_custom_themes` (optional)
A list of drupal custom themes. For example

```
drupal_custome_themes:
  - {src_name: avoindata-drupal-theme, theme_name: avoindata }

```

#### `drupal_language_modules` (optional)
A list of drupal language modules. Defaults listed below:

```
drupal_language_modules:
- config_translation
- content_translation
- language
- locale
- drush_language

```

#### `drupal_extra_modules` (optional)
A list of drupal extra modules. Defaults listed below:

```
drupal_extra_modules:
- twig_tweak
- fontawesome_menu_icons
- smtp
```


External variables:

#### `www_root` (required)
Path to web root directory.

TODO: document role variables   

Dependencies
------------
Ansible roles php and composer. These are automatically included.

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: drupal, tags: drupal }

License
-------

MIT
