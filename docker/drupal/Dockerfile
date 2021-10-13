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

# install site config
COPY site_config /opt/drupal/site_config

# install translations
COPY i18n /opt/i18n

# install services.yml
COPY services.yml /opt/drupal/web/sites/default/services.yml

# install templates
COPY templates /opt/templates

# install entrypoint.sh
COPY scripts/ ./
RUN chmod +x *.sh

ENTRYPOINT ["./entrypoint.sh"]
