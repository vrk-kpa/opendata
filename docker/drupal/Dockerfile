FROM ubuntu:focal AS builder

# install required packages
RUN apt-get update -yq && apt-get install curl libjpeg-turbo8 -yq

# install nodejs via nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -yq nodejs && npm install -g gulp

# copy custom themes
COPY modules/avoindata-drupal-theme             /tmp/modules/avoindata-drupal-theme

# copy custom modules
COPY modules/avoindata-drupal-header            /tmp/modules/avoindata-drupal-header
COPY modules/avoindata-drupal-servicemessage    /tmp/modules/avoindata-drupal-servicemessage
COPY modules/avoindata-drupal-hero              /tmp/modules/avoindata-drupal-hero
COPY modules/avoindata-drupal-categories        /tmp/modules/avoindata-drupal-categories
COPY modules/avoindata-drupal-infobox           /tmp/modules/avoindata-drupal-infobox
COPY modules/avoindata-drupal-datasetlist       /tmp/modules/avoindata-drupal-datasetlist
COPY modules/avoindata-drupal-newsfeed          /tmp/modules/avoindata-drupal-newsfeed
COPY modules/avoindata-drupal-appfeed           /tmp/modules/avoindata-drupal-appfeed
COPY modules/avoindata-drupal-footer            /tmp/modules/avoindata-drupal-footer
COPY modules/avoindata-drupal-articles          /tmp/modules/avoindata-drupal-articles
COPY modules/avoindata-drupal-events            /tmp/modules/avoindata-drupal-events
COPY modules/avoindata-drupal-guide             /tmp/modules/avoindata-drupal-guide
COPY modules/avoindata-drupal-user              /tmp/modules/avoindata-drupal-user
COPY modules/avoindata-drupal-ckeditor-plugins  /tmp/modules/avoindata-drupal-ckeditor-plugins

# copy frontend module
COPY modules/ytp-assets-common                  /tmp/modules/ytp-assets-common
COPY docker/drupal/package.json                 /tmp/modules/ytp-assets-common/

# build custom theme
WORKDIR /tmp/modules/ytp-assets-common
RUN npm install --unsafe-perm=true --allow-root
RUN gulp
#RUN gulp copy:fontawesomeLess drupal
WORKDIR /tmp/modules
RUN cp -r /tmp/modules/ytp-assets-common/resources /tmp/resources && \
    rm -rf /tmp/modules/ytp-assets-common

FROM drupal:9-fpm-alpine

# NOTE: workdir is /opt/drupal
# NOTE: webroot is /opt/drupal/web
# NOTE: modules is /opt/drupal/modules

# install required pkgs
RUN apk add --no-cache unzip git postgresql-client py3-yaml && \
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

# install custom modules and symlink them with proper module names
COPY --from=builder /tmp/modules /opt/modules
RUN ln -sf /opt/modules/avoindata-drupal-header/              /opt/drupal/web/modules/avoindata-header && \
    ln -sf /opt/modules/avoindata-drupal-servicemessage/      /opt/drupal/web/modules/avoindata-servicemessage && \
    ln -sf /opt/modules/avoindata-drupal-hero/                /opt/drupal/web/modules/avoindata-hero && \
    ln -sf /opt/modules/avoindata-drupal-categories/          /opt/drupal/web/modules/avoindata-categories && \
    ln -sf /opt/modules/avoindata-drupal-infobox/             /opt/drupal/web/modules/avoindata-infobox && \
    ln -sf /opt/modules/avoindata-drupal-datasetlist/         /opt/drupal/web/modules/avoindata-datasetlist && \
    ln -sf /opt/modules/avoindata-drupal-newsfeed/            /opt/drupal/web/modules/avoindata-newsfeed && \
    ln -sf /opt/modules/avoindata-drupal-appfeed/             /opt/drupal/web/modules/avoindata-appfeed && \
    ln -sf /opt/modules/avoindata-drupal-footer/              /opt/drupal/web/modules/avoindata-footer && \
    ln -sf /opt/modules/avoindata-drupal-articles/            /opt/drupal/web/modules/avoindata-articles && \
    ln -sf /opt/modules/avoindata-drupal-events/              /opt/drupal/web/modules/avoindata-events && \
    ln -sf /opt/modules/avoindata-drupal-guide/               /opt/drupal/web/modules/avoindata-guide && \
    ln -sf /opt/modules/avoindata-drupal-user/                /opt/drupal/web/modules/avoindata-user && \
    ln -sf /opt/modules/avoindata-drupal-ckeditor-plugins/    /opt/drupal/web/modules/avoindata-ckeditor-plugins

# install resources, symlink custom theme and install fonts
COPY --from=builder /tmp/resources /opt/resources
RUN ln -sf /opt/modules/avoindata-drupal-theme/                         /opt/drupal/web/themes/avoindata && \
    cp -r /opt/resources/vendor/@fortawesome/fontawesome/webfonts/      /opt/drupal/web/themes/avoindata/fonts && \
    cp -r /opt/resources/vendor/bootstrap/dist/fonts/                   /opt/drupal/web/themes/avoindata/fonts

# install site config
COPY docker/drupal/site_config /opt/drupal/site_config

# install translations
COPY docker/drupal/i18n /opt/i18n

# install services.yml and settings.php
COPY docker/drupal/services.yml /opt/drupal/web/sites/default/services.yml
COPY docker/drupal/settings.php /opt/drupal/web/sites/default/settings.php

# install templates
COPY docker/drupal/templates /opt/templates

# install entrypoint.sh
COPY docker/drupal/scripts/ ./
RUN chmod +x *.sh

ENTRYPOINT ["./entrypoint.sh"]
