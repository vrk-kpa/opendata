# docker

This folder contains dockerized versions of the opendata services.

## Files & folders

* files
  * .env.*.local
    * variable files for local env containers
  * .mh-auth
    * htpasswd file for local env smtp (mailhog) server
      * username=test
      * password=test
* folders
  * ckan/
    * CKAN docker image
    * Build context is docker/ckan/
  * datapusher/
    * Datapusher docker image
    * Build context is docker/datapusher/
  * drupal/
    * Drupal docker image
    * Build context is repository root
      * This is because the Dockerfile needs access to modules/
  * nginx/
    * NGINX docker image
    * Build context is docker/nginx/
  * solr/
    * Solr docker image
    * Build context is docker/solr/
  * postgres/
    * PostgrSQL / PostGIS docker image, for local env
    * Build context is docker/postgres/

## Basic local environment operations

### Build & run
```bash
docker-compose --env-file docker/.env.local up --build -d
```

### Scale service X to N containers
```bash
docker-compose --env-file docker/.env.local up --scale X=N -d
```

### Example, scaling drupal to 5 instances
```bash
docker-compose --env-file docker/.env.local up --scale drupal=5 -d
```

## Services that currently support scaling in local environment

* drupal
