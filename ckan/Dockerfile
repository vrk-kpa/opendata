# build args
ARG SECRET_NPMRC
ARG DYNATRACE_ENABLED=0

#
# CKAN build
#
FROM ghcr.io/keitaroinc/ckan:2.9.5-focal AS ckan_build

# switch from ckan to root user
USER root

# upgrade system + install required packages
RUN apt-get update -yq && \
    apt-get upgrade -yq && \
    apt-get install -yq \
      build-essential \
      unzip \
      zip \
      cron \
      rsync \
      postgresql-client \
      libpq-dev \
      libxslt1-dev \
      zlib1g-dev \
      libgeos-c1v5 \
      libxml2-dev \
      libssl-dev \
      libffi-dev \
      file && \
    pip install \
      jinja2-cli \
      supervisor \
      cryptography \
      ndg-httpsclient \
      pyasn1 \
      polib \
      botocore \
      boto \
      boto3

# setup env vars, from base image:
# - APP_DIR=/srv/app
# - SRC_DIR=/srv/app/src
# - DATA_DIR=/srv/app/data
ENV SUPERV_DIR=${APP_DIR}/supervisor
ENV CRON_DIR=${APP_DIR}/cron
ENV SCRIPT_DIR=${APP_DIR}/scripts
ENV TEMPLATE_DIR=${APP_DIR}/templates
ENV EXT_DIR=${APP_DIR}/ckanext
ENV WWW_DIR=/var/www

# copy app files
COPY scripts ${SCRIPT_DIR}
COPY data ${DATA_DIR}_base
COPY templates ${TEMPLATE_DIR}
COPY supervisor ${SUPERV_DIR}
COPY cron ${CRON_DIR}
COPY src/ckan/patches ${SRC_DIR}/ckan/patches
COPY src/ckan/ckan-uwsgi.ini ${APP_DIR}
RUN chmod +x ${SCRIPT_DIR}/*.sh && \
    rm -f ${APP_DIR}/production.ini && \
    rm -f ${APP_DIR}/ckan.ini && \
    rm -f ${APP_DIR}/who.ini && \
    mkdir -p ${WWW_DIR}

# apply patches
# NOTE: autodynatrace patch added later in this file
RUN cd ${SRC_DIR}/ckan && \
    patch --strip=1 --input=patches/enable_multiple_image_uploads.patch && \
    patch --strip=1 --input=patches/remove-ckan-fontawesome.patch && \
    patch --strip=1 --input=patches/optimize_group_show.patch && \
    patch --strip=1 --input=patches/optimize_template_loading.patch && \
    patch --strip=1 --input=patches/group_include_extras.patch && \
    patch --strip=1 --input=patches/remove_gravatar.patch && \
    patch --strip=1 --input=patches/json_serializable_lazyjsonobject.patch && \
    patch --strip=1 --input=patches/implement_is_required_for_image_upload.patch && \
    patch --strip=1 --input=patches/add_drafts_to_search.patch && \
    patch --strip=1 --input=patches/ignore_write_errors.patch && \
    patch --strip=1 --input=patches/fix_user_in_caching_logic.patch && \
    patch --strip=1 --input=patches/add_prefix_to_werkzeug.patch

# install crontab
RUN chmod +x ${CRON_DIR}/scripts/*.sh && \
    crontab -u ckan ${CRON_DIR}/crontab && \
    chmod u+s /usr/sbin/cron


#
# Development image (for local development)
#
FROM ckan_build AS ckan_development

ENV DEV_MODE=true

# install ckan dev requirements
RUN pip install -r ${SRC_DIR}/ckan/dev-requirements.txt

# enable sudo for ckan user
RUN apt-get install -yq sudo && \
    adduser ckan sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# fix permissions
RUN chown -R ckan:ckan ${APP_DIR}

# switch from root to ckan user
USER ckan

ENTRYPOINT ["/srv/app/scripts/entrypoint_ckan.sh"]

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
ENV APP_DIR=/srv/app
ENV EXT_DIR=${APP_DIR}/ckanext

# copy custom modules
RUN mkdir -p ${EXT_DIR} && mkdir -p ${APP_DIR}/frontend
COPY ckanext/ckanext-drupal8                ${EXT_DIR}/ckanext-drupal8/
COPY ckanext/ckanext-ytp_drupal             ${EXT_DIR}/ckanext-ytp_drupal/
COPY ckanext/ckanext-ytp_tasks              ${EXT_DIR}/ckanext-ytp_tasks/
COPY ckanext/ckanext-ytp_request            ${EXT_DIR}/ckanext-ytp_request/
COPY ckanext/ckanext-ytp_main               ${EXT_DIR}/ckanext-ytp_main/
COPY ckanext/ckanext-hierarchy              ${EXT_DIR}/ckanext-hierarchy/
COPY ckanext/ckanext-matomo                 ${EXT_DIR}/ckanext-matomo/
COPY ckanext/ckanext-datarequests           ${EXT_DIR}/ckanext-datarequests/
COPY ckanext/ckanext-harvest                ${EXT_DIR}/ckanext-harvest/
COPY ckanext/ckanext-report                 ${EXT_DIR}/ckanext-report/
COPY ckanext/ckanext-spatial                ${EXT_DIR}/ckanext-spatial/
COPY ckanext/ckanext-dcat                   ${EXT_DIR}/ckanext-dcat/
COPY ckanext/ckanext-cloudstorage           ${EXT_DIR}/ckanext-cloudstorage/
COPY ckanext/ckanext-scheming               ${EXT_DIR}/ckanext-scheming/
COPY ckanext/ckanext-fluent                 ${EXT_DIR}/ckanext-fluent/
COPY ckanext/ckanext-showcase               ${EXT_DIR}/ckanext-showcase/
COPY ckanext/ckanext-sixodp_showcase        ${EXT_DIR}/ckanext-sixodp_showcase/
COPY ckanext/ckanext-sixodp_showcasesubmit  ${EXT_DIR}/ckanext-sixodp_showcasesubmit/
COPY ckanext/ckanext-geoview                ${EXT_DIR}/ckanext-geoview/
COPY ckanext/ckanext-pdfview                ${EXT_DIR}/ckanext-pdfview/
COPY ckanext/ckanext-disqus                 ${EXT_DIR}/ckanext-disqus/
COPY ckanext/ckanext-reminder               ${EXT_DIR}/ckanext-reminder/
COPY ckanext/ckanext-archiver               ${EXT_DIR}/ckanext-archiver/
COPY ckanext/ckanext-qa                     ${EXT_DIR}/ckanext-qa/
COPY ckanext/ckanext-organizationapproval   ${EXT_DIR}/ckanext-organizationapproval/
COPY ckanext/ckanext-advancedsearch         ${EXT_DIR}/ckanext-advancedsearch/
COPY ckanext/ckanext-forcetranslation       ${EXT_DIR}/ckanext-forcetranslation/
COPY ckanext/ckanext-apis                   ${EXT_DIR}/ckanext-apis/
COPY ckanext/ckanext-prh_tools              ${EXT_DIR}/ckanext-prh_tools/
COPY ckanext/ckanext-openapiviewer          ${EXT_DIR}/ckanext-openapiviewer/
COPY ckanext/ckanext-statistics             ${EXT_DIR}/ckanext-statistics/
COPY ckanext/ckanext-sentry                 ${EXT_DIR}/ckanext-sentry/
COPY ckanext/ckanext-ytp_recommendation     ${EXT_DIR}/ckanext-ytp_recommendation/

#
# Production stage, dynatrace enabled
#
FROM ckan_build AS production-dynatrace-1

# install dynatrace oneagent
# https://www.dynatrace.com/support/help/setup-and-configuration/setup-on-cloud-platforms/amazon-web-services/deploy-oneagent-on-aws-fargate
COPY --from=ayv41550.live.dynatrace.com/linux/oneagent-codemodules:sdk / /
ENV LD_PRELOAD=/opt/dynatrace/oneagent/agent/lib64/liboneagentproc.so

# install autodynatrace
RUN pip install autodynatrace

# apply patches
RUN cd ${SRC_DIR}/ckan && \
    patch --strip=1 --input=patches/add_autodynatrace.patch

#
# Production stage, dynatrace disabled
#
FROM ckan_build AS production-dynatrace-0

# do nothing :^)

#
# Production image
#
FROM production-dynatrace-${DYNATRACE_ENABLED} AS production

# copy extensions
COPY --from=modules_build ${EXT_DIR} ${EXT_DIR}

# install extensions
RUN ${SCRIPT_DIR}/install_extensions.sh

# lock certain python package versions for compatibility
RUN pip install \
    flask==0.12 \
    flask-login==0.3.0 \
    simplejson==3.16.0 \
    six==1.13.0

# fix permissions
RUN chown -R ckan:ckan ${APP_DIR}

# switch from root to ckan user
USER ckan

ENTRYPOINT ["/srv/app/scripts/entrypoint_ckan.sh"]
