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

# set workdir to frontend module & copy package.json
WORKDIR /opt/drupal_modules/ytp-assets-common
COPY docker/package.default.json /opt/drupal_modules/ytp-assets-common/package.json

# build frontend
RUN npm install --unsafe-perm=true --allow-root && gulp

#
# Drupal build
#
FROM drupal:9-fpm-alpine

# NOTE: workdir is /opt/drupal
# NOTE: webroot is /opt/drupal/web
# NOTE: modules is /opt/drupal/modules

# install required pkgs
RUN apk add --no-cache unzip git postgresql-client py3-yaml && \
    apk add --no-cache jinja2-cli --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing && \
    apk add --no-cache python3

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
    drupal/ape \
    drupal/bootstrap \
    drupal/coder \
    drupal/console \
    drupal/disqus \
    drupal/domain_registration \
    drupal/drush_language \
    drupal/easy_breadcrumb \
    drupal/easy_install \
    drupal/fontawesome_menu_icons \
    drupal/honeypot \
    drupal/libraries \
    drupal/matomo \
    drupal/menu_item_role_access \
    drupal/metatag \
    drupal/pathauto \
    drupal/protected_submissions \
    drupal/recaptcha \
    drupal/redirect \
    drupal/search_api \
    drupal/smtp \
    drupal/token \
    drupal/twig_field_value \
    drupal/twig_tweak \
    drupal/unpublished_node_permissions \
    drupal/upgrade_status \
    drush/drush \
    vlucas/phpdotenv \
    webflo/drupal-finder \
    webmozart/path-util \
    cweagans/composer-patches \
    league/commonmark ^1.5

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

ENTRYPOINT ["./entrypoint.sh"]
