
## Avoindata.fi [![CircleCI][circleci-image]][circleci-url] [![Cypress Dashboard](https://img.shields.io/badge/cypress-dashboard-brightgreen.svg)](https://dashboard.cypress.io/#/projects/ssb2ut/runs)

Main repository for Yhteentoimivuuspalvelut (_Interoperability services_ in Finnish). This service combines two related subservices:

- [Avoindata.fi](https://www.avoindata.fi/), a search engine and metadata catalog for Finnish open data
- A catalog of interoperability tools and guidelines

The service is publicly available at [Avoindata.fi](https://www.avoindata.fi/). Free registration is required for features such as commenting and publishing of datasets. A developer sandbox is also available at [betaavoindata.fi](http://betaavoindata.fi) or [betaopendata.fi](http://betaopendata.fi).

This source repository contains:

- Configuration management scripts ([Ansible](http://www.ansible.com))
- Tools for local development ([Vagrant](http://www.vagrantup.com))
- Configuration for Continuous integration ([Circle](https://circleci.com/gh/vrk-kpa/opendata))
- Source code as submodules under the _modules_ directory

### Getting started

To try out the service, visit the sandbox/development environment [betaavoindata.fi](http://betaavoindata.fi) or the production environment [avoindata.fi](http://avoindata.fi), and register a user account to create new datasets.

To get started in developing the software, install a local development environment as described in the [documentation](doc/local-installation.md), and then see the [development documentation](doc/local-development.md).

### Documentation

Please refer to the [documentation directory](doc) and [API documentation](https://github.com/vrk-kpa/ytp-api).

### Contact

Please file [issues at Github](https://github.com/vrk-kpa/ytp/issues).

### Copying and License

This material is copyright (c) 2013-2021 Digital and Population Data Services Agency, Finland.

CKAN extensions and Drupal components are licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at: http://www.fsf.org/licensing/licenses/agpl-3.0.html

All other content in this repository is licensed under MIT License unless otherwise specified.

### External services used during development

Some of the external services used.

<img src="/doc/images/Browserstack-logo.svg" width=200>

Browserstack is used to test the service with different browsers and devices.

[circleci-url]: https://circleci.com/gh/vrk-kpa/opendata
[circleci-image]: https://circleci.com/gh/vrk-kpa/opendata.svg?style=svg
