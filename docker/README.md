# docker

This folder contains dockerized versions of the opendata services.

This is a work in progress.

## Files & folders

* files
  * .env.*.local
    * variable files for local env containers
  * .mh-auth
    * htpasswd file for local env smtp (mailhog) server
      * username=test
      * password=test
  * package.default.json
    * package.json with fontawesome-free for modules/ytp-assets-common
* folders
  * ckan/
    * CKAN docker image
    * Build context is repository root
      * This is because the Dockerfile needs access to modules/
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

Common configuration template is contained in `docker/.env.local.template`. Developers must copy this file into `docker/.env.local` and edit it to their likings. The `docker/.env.local` file is ignored in version control.

The template contains an already working configuration to get started.

## Local environment operations

### Build & run
```bash
# bring docker compose stack up with current latest images + force rebuild of all images
docker-compose -p opendata --env-file docker/.env.local up --build -d
```

### Build with secrets & run
```bash
# build drupal image using BuildKit secrets
docker build --no-cache -t opendata/drupal:latest --secret id=npmrc,src=./modules/ytp-assets-common/.npmrc --file=./docker/drupal/Dockerfile .
# build ckan image using BuildKit secrets
docker build --no-cache -t opendata/ckan:latest --secret id=npmrc,src=./modules/ytp-assets-common/.npmrc --file=./docker/ckan/Dockerfile .
# bring docker compose stack up with current latest images
docker-compose -p opendata --env-file docker/.env.local up -d
```

### Stop
```bash
# bring docker compose stack down, not destroying persistent volumes
docker-compose -p opendata down
```

### Destroy
```bash
# destroy docker compose stack, destroys persistent volumes
docker-compose -p opendata down --volumes
```

### Example: Scale service X to N containers
```bash
docker-compose -p opendata --env-file docker/.env.local up --scale X=N -d
```

### Example: scaling drupal to 5 instances
```bash
docker-compose -p opendata --env-file docker/.env.local up --scale drupal=5 -d
```

## Services that currently support scaling in local environment

* drupal
* ckan
