#
# Frontend build
#
FROM ubuntu:focal AS frontend_builder

# install required packages
RUN apt-get update -yq && apt-get install curl libjpeg-turbo8 build-essential autoconf -yq

# install nodejs via nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -yq nodejs && npm install -g gulp

# copy custom modules
COPY modules /opt/drupal_modules/

# set workdir, copy default package.json, import .npmrc as secret and run build script
WORKDIR /opt/drupal_modules/ytp-assets-common
COPY docker/package.default.json /opt/drupal_modules/ytp-assets-common/package.default.json
COPY --chmod=+x docker/build_frontend.sh /opt/drupal_modules/ytp-assets-common/build_frontend.sh
RUN --mount=type=secret,id=npmrc ./build_frontend.sh

#
# Drupal build
#
FROM drupal:9-fpm-alpine

# NOTE: workdir is /opt/drupal
# NOTE: webroot is /opt/drupal/web
# NOTE: modules is /opt/drupal/modules

# install required pkgs
RUN apk add --no-cache unzip git postgresql-client py3-yaml rsync python3 && \
    apk add --no-cache jinja2-cli --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing

# make sure config sync directory exists
RUN mkdir -p /opt/drupal/web/sites/default/sync && \
    chown -R www-data:www-data /opt/drupal/web/sites/default/sync

# make sure public files directory exists
RUN mkdir -p /opt/drupal/web/sites/default/files && \
    chown -R www-data:www-data /opt/drupal/web/sites/default/files

# configure composer
RUN composer config minimum-stability dev && \
    composer config prefer-stable true

# install composer deps
# NOTE: default pkgs: composer/installers, drupal/core-composer-scaffold, drupal/core-project-message, drupal/core-recommended
RUN composer require --dev --no-cache \
    drupal/core-dev \
    squizlabs/php_codesniffer \
    dealerdirect/phpcodesniffer-composer-installer \
&& \
    composer require --no-cache \
    "cweagans/composer-patches:^1.7" \
    "drupal/ape:^1.4" \
    "drupal/bootstrap:^3.9" \
    "drupal/coder:^8.2" \
    "drupal/console:^1.0.2" \
    "drupal/disqus:^1.0@RC" \
    "drupal/domain_registration:^1.6" \
    "drupal/drush_language:1.x-dev" \
    "drupal/easy_breadcrumb:^1.8" \
    "drupal/easy_install:^10.2" \
    "drupal/fontawesome_menu_icons:^1.3" \
    "drupal/honeypot:^2.0" \
    "drupal/libraries:^3.0@alpha" \
    "drupal/matomo:^1.11" \
    "drupal/menu_item_role_access:^2.0" \
    "drupal/metatag:^1.7" \
    "drupal/pathauto:^1.2" \
    "drupal/protected_submissions:^1.9" \
    "drupal/recaptcha:^3.0" \
    "drupal/redirect:^1.2" \
    "drupal/search_api:^1.10" \
    "drupal/smtp:^1.0" \
    "drupal/token:^1.5" \
    "drupal/twig_field_value:^2.0" \
    "drupal/twig_tweak:^2.0" \
    "drupal/unpublished_node_permissions:^1.0" \
    "drupal/upgrade_status:^3.10" \
    "drush/drush:^10.0.0" \
    "league/commonmark:^1.5" \
    "vlucas/phpdotenv:^2.4" \
    "webflo/drupal-finder:^1.0.0" \
    "webmozart/path-util:^2.3"

# install custom modules
ENV MOD_DIR=/opt/drupal_modules
COPY --from=frontend_builder /opt/drupal_modules ${MOD_DIR}/

# install static resources
ENV WWW_DIR=/var/www
ENV RES_DIR=${WWW_DIR}/resources
RUN mkdir -p ${WWW_DIR} && mv ${MOD_DIR}/ytp-assets-common/resources ${WWW_DIR}/

# install site config
COPY docker/drupal/site_config /opt/drupal/site_config

# install translations
COPY docker/drupal/i18n /opt/i18n

# install services.yml
COPY docker/drupal/services.yml /opt/drupal/web/sites/default/services.yml

# install templates
COPY docker/drupal/templates /opt/templates

# install entrypoint.sh
COPY docker/drupal/scripts/ ./
RUN chmod +x *.sh

# setup shared base directories
RUN mkdir -p /opt/base && \
    mv /opt/drupal/web /opt/base/web && \
    mv /var/www/resources /opt/base/resources

ENTRYPOINT ["./entrypoint.sh"]
