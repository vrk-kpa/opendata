
## Avoindata.fi [![CircleCI][circleci-image]][circleci-url] [![Cypress Dashboard](https://img.shields.io/badge/cypress-dashboard-brightgreen.svg)](https://dashboard.cypress.io/#/projects/ssb2ut/runs)

Main repository for Yhteentoimivuuspalvelut (_Interoperability services_ in Finnish). This service combines two related subservices:

- [Avoindata.fi](https://www.avoindata.fi/), a search engine and metadata catalog for Finnish open data
- A catalog of interoperability tools and guidelines

The service is publicly available at [Avoindata.fi](https://www.avoindata.fi/). Free registration is required for features such as commenting and publishing of datasets. A developer sandbox is also available at [betaavoindata.fi](http://betaavoindata.fi) or [betaopendata.fi](http://betaopendata.fi).

### Getting started

To try out the service, visit the sandbox/development environment [betaavoindata.fi](http://betaavoindata.fi) or the production environment [avoindata.fi](http://avoindata.fi), and register a user account to create new datasets.

To get started in developing the software, install a local development environment as described in the [documentation](doc/local-installation.md), and then see the [development documentation](doc/local-development.md).

### Documentation

Please refer to the [documentation directory](doc) and [API documentation](https://github.com/vrk-kpa/ytp-api).

### Contact

Please file [issues at Github](https://github.com/vrk-kpa/opendata/issues).

## List of CKAN extensions

| :sunglasses: | Name | Description |
|---|---|---|
| :bookmark_tabs: | [ckanext-orgdashboards](https://github.com/ViderumGlobal/ckanext-orgdashboards) | CKAN extension for creating organization dashboards.
| :chart_with_upwards_trend: | [ckanext-matomo](https://github.com/vrk-kpa/ckanext-matomo) | CKAN extension to integrate Matomo data into CKAN. Gives download stats on package pages, list of most popular packages, etc.
| :tractor: | [ckanext-harvest](https://github.com/ckan/ckanext-harvest) | This extension provides a common harvesting framework for ckan extensions and adds a CLI and a WUI to CKAN to manage harvesting sources and jobs.
| :milky_way: | [ckanext-spatial](https://github.com/ckan/ckanext-spatial) | This extension contains plugins that add geospatial capabilities to CKAN.
| :watch: | [ckanext-realtime](https://github.com/alexandrainst/ckanext-realtime) | CKAN plugin which makes your CKAN site into a Realtime Data Portal.
| :earth_americas: | [ckanext-dataspatial](https://github.com/NaturalHistoryMuseum/ckanext-dataspatial) | Dataspatial is a Ckan extension to provide geospatial awareness of datastore data.
| :mailbox_with_mail: | [ckanext-requestdata](https://github.com/ViderumGlobal/ckanext-requestdata) | This extension introduces a new type of dataset in which access to data is by request.
| :bookmark_tabs: | [ckanext-orgportals](https://github.com/ViderumGlobal/ckanext-orgportals) | CKAN extension for creating organization portals.
| :mag_right: | [Data Solr](https://github.com/NaturalHistoryMuseum/ckanext-datasolr) | Datasolr is a Ckan extension to use Solr for datastore queries.
| :closed_lock_with_key: | [ckanext-cas](https://github.com/keitaroinc/ckanext-cas) | CAS (Central Authentication Service) client extension for CKAN.
| :dvd: | [ckanext-s3filestore](https://github.com/keitaroinc/ckanext-s3filestore) | Use Amazon S3 as a filestore for CKAN.
| :bar_chart: | [ckanext-c3charts](https://github.com/ViderumGlobal/ckanext-c3charts) | c3js based charts for CKAN.
| :truck: | [ckanext-cloudstorage](https://github.com/TkTech/ckanext-cloudstorage) | Implements support for resource storage against multiple popular providers via apache-libcloud (S3, Azure Storage, etc...).
| :station: | [ckanext-dcat](https://github.com/ckan/ckanext-dcat) | This extension provides plugins that allow CKAN to expose and consume metadata from other catalogs using RDF documents serialized using DCAT.
| :speak_no_evil: | [ckanext-fluent](https://github.com/ckan/ckanext-fluent) | This extension provides a way to store and return multilingul fields in CKAN datasets, resources, organizations and groups.
| :japan: | [ckanext-mapviews](https://github.com/ckan/ckanext-mapviews) | CKAN Resource View to build maps and choropleth maps.
| :open_file_folder: | [ckanext-odata](https://github.com/jqnatividad/ckanext-odata) | CKAN OData support to connect to tools like Tableau.
| :notebook: | [ckanext-pages](https://github.com/ckan/ckanext-pages) | This extension gives you an easy way to add simple pages to CKAN.
| :earth_africa: | [ckanext-spatial](https://github.com/ckan/ckanext-spatial) | This extension contains plugins that add geospatial capabilities to CKAN.
| :fast_forward: | [ckanext-xloader](https://github.com/ckan/ckanext-xloader) | Designed as a replacement for DataPusher because it offers ten times the speed and more robustness.


### Copying and License

This material is copyright (c) 2013-2022 Digital and Population Data Services Agency, Finland.

CKAN extensions and Drupal components are licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at: http://www.fsf.org/licensing/licenses/agpl-3.0.html

All other content in this repository is licensed under MIT License unless otherwise specified.

### External services used during development

Some of the external services used.

<img src="/doc/images/Browserstack-logo.svg" width=200>

Browserstack is used to test the service with different browsers and devices.

[circleci-url]: https://circleci.com/gh/vrk-kpa/opendata
[circleci-image]: https://circleci.com/gh/vrk-kpa/opendata.svg?style=svg
