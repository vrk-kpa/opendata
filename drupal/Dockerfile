# build args
ARG SECRET_NPMRC

#
# Drupal build
#
FROM drupal:9.5.8-php8.1-apache-buster AS drupal_build

# upgrade system + install required packages
RUN apt-get update -yq && \
    apt-get upgrade -yq && \
    apt-get install -yq \
      unzip \
      git \
      rsync \
      postgresql-client \
      python3 \
      python3-pip \
      procps && \
    pip3 install \
      jinja2-cli

# setup env vars
ENV APP_DIR=/opt/drupal
ENV SCRIPT_DIR=${APP_DIR}/scripts
ENV TEMPLATE_DIR=${APP_DIR}/templates
ENV I18N_DIR=${APP_DIR}/i18n
ENV WEB_DIR=${APP_DIR}/web
ENV SITE_DIR=${WEB_DIR}/sites
ENV MOD_DIR=${WEB_DIR}/modules
ENV THEME_DIR=${WEB_DIR}/themes
ENV CORE_DIR=${WEB_DIR}/core
ENV DATA_DIR=${SITE_DIR}/default/files
ENV WWW_DIR=/var/www
ENV LOCAL_PHP_DIR=/usr/local/etc/php/

# copy the php.ini file for php configuration options
COPY configurations/uploads.ini ${LOCAL_PHP_DIR}/conf.d/

# copy app files
COPY i18n ${I18N_DIR}
COPY scripts ${SCRIPT_DIR}
COPY site_config ${APP_DIR}/site_config
COPY templates ${TEMPLATE_DIR}
COPY composer.json ${APP_DIR}/composer.json
COPY composer.lock ${APP_DIR}/composer.lock
RUN chmod +x ${SCRIPT_DIR}/*.sh && \
    mkdir -p ${SITE_DIR}/default/sync && \
    chown -R www-data:www-data ${SITE_DIR}/default/sync && \
    mkdir -p ${SITE_DIR}/default/files && \
    chown -R www-data:www-data ${SITE_DIR}/default/files

# install composer project
RUN composer install --no-cache --no-dev


#
# Development image (For local development)
#
FROM drupal_build as drupal_development

ENV DEV_MODE=true

# install drupal dev requirements
RUN composer install --no-cache --dev

ENTRYPOINT ["/opt/drupal/scripts/entrypoint.sh"]

#
# Modules build (for production)
#
FROM ubuntu:focal AS modules_build

# install required packages
RUN apt-get update -yq && apt-get install -yq curl

# install nodejs via nodesource & frontend requirements
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -yq nodejs libjpeg-turbo8

# setup env vars:
ENV APP_DIR=/opt/drupal
ENV WEB_DIR=${APP_DIR}/web
ENV MOD_DIR=${WEB_DIR}/modules

# copy custom modules
RUN mkdir -p ${MOD_DIR} && mkdir -p ${WEB_DIR}/frontend
COPY modules/avoindata-header               ${MOD_DIR}/avoindata-header/
COPY modules/avoindata-servicemessage       ${MOD_DIR}/avoindata-servicemessage/
COPY modules/avoindata-hero                 ${MOD_DIR}/avoindata-hero/
COPY modules/avoindata-categories           ${MOD_DIR}/avoindata-categories/
COPY modules/avoindata-infobox              ${MOD_DIR}/avoindata-infobox/
COPY modules/avoindata-explore              ${MOD_DIR}/avoindata-explore/
COPY modules/avoindata-newsfeed             ${MOD_DIR}/avoindata-newsfeed/
COPY modules/avoindata-footer               ${MOD_DIR}/avoindata-footer/
COPY modules/avoindata-articles             ${MOD_DIR}/avoindata-articles/
COPY modules/avoindata-events               ${MOD_DIR}/avoindata-events/
COPY modules/avoindata-guide                ${MOD_DIR}/avoindata-guide/
COPY modules/avoindata-user                 ${MOD_DIR}/avoindata-user/
COPY modules/avoindata-ckeditor-plugins     ${MOD_DIR}/avoindata-ckeditor-plugins/
COPY modules/avoindata-theme                ${MOD_DIR}/avoindata-theme/
COPY modules/avoindata-ckeditor5-plugins    ${MOD_DIR}/avoindata-ckeditor5-plugins/


#
# Production image
#
FROM drupal_build AS production

# copy modules and themes
COPY --from=modules_build ${MOD_DIR} ${MOD_DIR}
RUN mv ${MOD_DIR}/avoindata-theme ${THEME_DIR}/avoindata/

ENTRYPOINT ["/opt/drupal/scripts/entrypoint.sh"]
