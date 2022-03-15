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

Buildkit might be enabled by default, but if the docker builds give you errors, you might want to verify it's enabled by following the instructions below.

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

## Local environment secrets (not required)

By default, the local setup will build the ckan and drupal image frontends using free version of fontawesome.

To use the pro version, you must provide a valid .npmrc file either via BuildKit secrets or Dockerfile build-time ARG. BuildKit secrets are meant for production image builds because they provide a secure way to use secrets during image builds. For local development, use the build-time ARG option instead because it is supported in docker-compose builds.

## Steps for setting up the local dev environment

If you're not on MacOS, make sure you have enabled Buildkit for docker and docker-compose as mentioned above for your system.

0. Make sure you have copied the `docker/.env.template` to `docker/.env` as mentioned above.

1. Create a file `docker-compose.override.yml` to the `docker` directory and populate its contents with the example below (next topic)

2. Clone the following repos to the {root} path:
  - opendata (https://github.com/vrk-kpa/opendata)
  - opendata-ckan (https://github.com/vrk-kpa/opendata-ckan)
  - opendata-drupal (https://github.com/vrk-kpa/opendata-drupal)
  - opendata-nginx (https://github.com/vrk-kpa/opendata-nginx)
  - opendata-solr (https://github.com/vrk-kpa/opendata-solr)

3. Run `git submodule update --init --recursive` in opendata-ckan and opendata-drupal repo directories

4. Create a `.npmrc` (content below) file to this directory and copy it to the following places:  `../../opendata-ckan/frontend` and `../../opendata-drupal/frontend`. Link to .npmrc content: `https://wiki.dvv.fi/display/AV/Font+Awesome+Pro`

5. (Only on MacOS and Windows) Make sure buildkit is enabled in Docker Desktop. Go to Preferences -> Docker Engine, it should contain this:
```
"features": {
  "buildkit": true
}
```

6. (Only on MacOS) Go to Docker Desktop's Dashboard, open settings and navigate to `Resources` -> `File Sharing`. Add the directories to the repos you cloned in step 2 to the list

7. Build assets in `../../opendata-ckan/frontend` and `../../opendata-drupal/frontend` with `npm install && npm run gulp`

8. Run `docker-compose up --build` in the docker directory. Once this is done, navigate to `localhost` in the browser (the avoindata site should run on port 80).


## Example docker-compose.override.yml for local development

Create a file `docker-compose.override.yml` to the `docker` directory and populate its contents with the example below.
This file is automatically detected by docker-compose so you don't need to pass it in commands, it just works.

```yml
# NOTE: This file is also in .gitignore, please keep it that way!
# NOTE: This example assumes you have cloned opendata-ckan and opendata-drupal repos to ../../ path.
# NOTE: We don't want node_modules in our bind-mount, thus we mask it with empty volume!
# NOTE: Remember to build the `opendata-assets` frontend project on the host machine!
version: "3.8"

services:
  ckan:
    image: opendata/ckan:latest
    build:
      context: ../../opendata-ckan
      target: ckan_development
    ports:
      - "5000:5000"
    environment:
      AWS_ACCESS_KEY_ID: "temp-access-key-if-using-ckanext-cloudstorage"
      AWS_SECRET_ACCESS_KEY: "temp-secret-key-if-using-ckanext-cloudstorage"
      AWS_DEFAULT_REGION: "eu-west-1"
    volumes:
      - ../../opendata-ckan/modules:/srv/app/modules
      - /srv/app/modules/opendata-assets/node_modules/

  ckan_cron:
    image: opendata/ckan:latest
    build:
      context: ../../opendata-ckan
      target: ckan_development
    volumes:
      # Override the entrypoint script with the one in opendata-ckan
      - ../../opendata-ckan/ckan/scripts/entrypoint_cron.sh:/srv/app/scripts/entrypoint_cron.sh
      # Mount the rest of the override files to be installed by entrypoint_cron.sh
      - ../../opendata-ckan/ckan:/srv/app/overrides
      - ../../opendata-ckan/modules:/srv/app/modules
      - /srv/app/modules/opendata-assets/node_modules/

  drupal:
    image: opendata/drupal:latest
    build:
      context: ../../opendata-drupal
      target: drupal_development
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
      - ../../opendata-drupal/modules/opendata-assets:/opt/drupal/web/modules/opendata-assets
      - ../../opendata-drupal/modules/avoindata-theme:/opt/drupal/web/themes/avoindata
      - /opt/drupal/web/modules/opendata-assets/node_modules/

  nginx:
    image: opendata/nginx:latest
    build:
      context: ../../opendata-nginx

  solr:
    image: opendata/solr:latest
    build:
      context: ../../opendata-solr
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

## Local environment problems

### WSL2 eats all memory

If your PC is low on memory, you might have problems running the containers under docker engine that's running via WSL2. In this case, you can adjust the maximum memory given to WSL2 by editing `C:\Users\{username}\.wslconfig`, below is an example of the file contents.

```ini
[wsl2]
memory=4GB
processors=2
```
