# docker

This folder contains dockerized versions of the opendata services.

## Files & folders

* files
  * .env
    * variable file shared between all services
  * .env.*.local
    * variable files for specific service
  * .mh-auth
    * htpasswd file for local env smtp (mailhog) server
      * username=test
      * password=test
* folders
  * postgres/
    * PostgrSQL / PostGIS docker image, for local env

## Build requirements

* docker engine 20.10.0+
  * `docker --version`
* docker-compose 1.25.0+
  * `docker-compose --version`
* buildkit enabled for docker

## Enabling buildkit

https://docs.docker.com/develop/develop-images/build_enhancements/

### Enable globally

Add the following `"buildkit": true` flag to your docker daemon config JSON file. Usually it resides in `/etc/docker/daemon.json`:
```
{
  "features":
  {
    "buildkit": true
  }
}
```

### Enable for terminal session

```
export DOCKER_BUILDKIT=1
```

### Instruct compose to use buildkit

```
export COMPOSE_DOCKER_CLI_BUILD=1
```

## Local environment configuration

Common configuration template is contained in `docker/.env.template`. Developers must copy this file into `docker/.env` and edit it to their likings. The `docker/.env` file is ignored in version control.

The template contains an already working configuration to get started.

## Local environment secrets

By default, the local setup will build the ckan and drupal image frontends using free version of fontawesome.

To use the pro version, you must provide a valid .npmrc file either via BuildKit secrets or Dockerfile build-time ARG. BuildKit secrets are meant for production image builds because they provide a secure way to use secrets during image builds. For local development, use the build-time ARG option instead because it is supported in docker-compose builds.

### Example docker-compose.override.yml for local development

Create a file `docker-compose.override.yml` to the `docker` directory and populate its contents with the example below and edit your .npmrc file contents in it appropriately.

This file is automatically detected by docker-compose so you don't need to pass it in commands, it just works.

```yml
# NOTE: This file is also in .gitignore, please keep it that way!
# NOTE: This example assumes you have cloned opendata-ckan and opendata-drupal repos to ../../ path.
# NOTE: We don't want node_modules in our bind-mount, thus we mask it with empty volume!
# NOTE: Remember to build the `ytp-assets-common` frontend project on the host machine!
version: "3.8"

services:
  ckan:
    image: opendata/ckan:latest
    build:
      context: ../../opendata-ckan
      target: ckan_development
      args:
        SECRET_NPMRC: |
          *multiline contents of the .npmrc file...*
          *...*
    ports:
      - "5000:5000"
    environment:
      AWS_ACCESS_KEY_ID: "temp-access-key-if-using-ckanext-cloudstorage"
      AWS_SECRET_ACCESS_KEY: "temp-secret-key-if-using-ckanext-cloudstorage"
      AWS_DEFAULT_REGION: "eu-west-1"
    volumes:
      - ../../opendata-ckan/modules:/srv/app/extensions
      - /srv/app/extensions/ytp-assets-common/node_modules/

  drupal:
    image: opendata/drupal:latest
    build:
      context: ../../opendata-drupal
      target: drupal_development
      args:
        SECRET_NPMRC: |
          *multiline contents of the .npmrc file...*
          *...*
    volumes:
      - ../../opendata-drupal/modules/avoindata-header/:/opt/drupal/web/modules/avoindata-header
      - ../../opendata-drupal/modules/avoindata-servicemessage/:/opt/drupal/web/modules/avoindata-servicemessage
      - ../../opendata-drupal/modules/avoindata-hero/:/opt/drupal/web/modules/avoindata-hero
      - ../../opendata-drupal/modules/avoindata-categories/:/opt/drupal/web/modules/avoindata-categories
      - ../../opendata-drupal/modules/avoindata-infobox/:/opt/drupal/web/modules/avoindata-infobox
      - ../../opendata-drupal/modules/avoindata-datasetlist/:/opt/drupal/web/modules/avoindata-datasetlist
      - ../../opendata-drupal/modules/avoindata-newsfeed/:/opt/drupal/web/modules/avoindata-newsfeed
      - ../../opendata-drupal/modules/avoindata-appfeed/:/opt/drupal/web/modules/avoindata-appfeed
      - ../../opendata-drupal/modules/avoindata-footer/:/opt/drupal/web/modules/avoindata-footer
      - ../../opendata-drupal/modules/avoindata-articles/:/opt/drupal/web/modules/avoindata-articles
      - ../../opendata-drupal/modules/avoindata-events/:/opt/drupal/web/modules/avoindata-events
      - ../../opendata-drupal/modules/avoindata-guide/:/opt/drupal/web/modules/avoindata-guide
      - ../../opendata-drupal/modules/avoindata-user/:/opt/drupal/web/modules/avoindata-user
      - ../../opendata-drupal/modules/avoindata-ckeditor-plugins/:/opt/drupal/web/modules/avoindata-ckeditor-plugins
      - ../../opendata-drupal/modules/ytp-assets-common:/opt/drupal/web/modules/ytp-assets-common
      - ../../opendata-drupal/modules/avoindata-theme:/opt/drupal/web/themes/avoindata
      - /opt/drupal/web/modules/ytp-assets-common/node_modules/
```

## Local environment operations

### Build/rebuild & create/recreate
```bash
docker-compose -p opendata up --build -d
```

### Bring services down
```bash
docker-compose -p opendata down
```

### Destroy services
```bash
docker-compose -p opendata down --volumes
```

### Example: Scale service X to N containers
```bash
docker-compose -p opendata up --scale X=N -d
```

### Example: scaling drupal to 5 instances
```bash
docker-compose -p opendata up --scale drupal=5 -d
```

## Services that currently support scaling in local environment

* drupal
* ckan
* datapusher

## Services that currently support scaling in AWS environment

* nginx
* drupal
* ckan
* datapusher
