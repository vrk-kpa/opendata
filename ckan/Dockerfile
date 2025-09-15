# build args
ARG SECRET_NPMRC

#
# Add common configuration to base image
#
FROM public.ecr.aws/docker/library/python:3.10.18-alpine3.22 AS configured_base

ENV APP_DIR=/srv/app
ENV SRC_DIR=${APP_DIR}/src
ENV CKAN_DIR=${SRC_DIR}/ckan \
    DATA_DIR=${APP_DIR}/data
WORKDIR ${APP_DIR}
COPY pip.conf /etc/pip.conf
RUN pip install --upgrade pip



#
# Build CKAN dependencies
#
FROM configured_base AS base_ckan_build

# Packages to build CKAN requirements and plugins
RUN \
  apk add --no-cache \
    bash \
    python3-dev \
    git \
    curl \
    postgresql-dev \
    linux-headers \
    gcc \
    make \
    g++ \
    autoconf \
    automake \
    libtool \
    patch \
    musl-dev \
    pcre-dev \
    pcre \
    libffi-dev \
    libxml2-dev \
    libxslt-dev

COPY ckan-requirements.txt .

RUN \
  # Create the src and pip cache directory
  mkdir -p ${SRC_DIR} && \
  # Fetch and build CKAN and requirements
  pip wheel --wheel-dir=/wheels -r ckan-requirements.txt


#
# Base CKAN image
#
FROM configured_base AS base_ckan

# Install necessary packages to run CKAN
RUN \
  apk add --no-cache \
      git \
      gettext \
      curl \
      postgresql-client \
      libmagic \
      pcre \
      libxslt \
      libxml2 \
      tzdata \
      file


# Get artifacts from build stages
COPY --from=base_ckan_build /wheels /srv/app/wheels

# Copy configuration
COPY ckan-requirements.txt ${SRC_DIR}/ckan-requirements.txt
COPY setup/app ${APP_DIR}

RUN \
  # Create SRC_DIR and DATA_DIR
  mkdir -p ${SRC_DIR} && \
  mkdir -p ${DATA_DIR} && \
  # Install CKAN and requirements
  pip install --find-links=/srv/app/wheels -r ${SRC_DIR}/ckan-requirements.txt && \
  pip install -e git+https://github.com/ckan/ckan.git@ckan-2.10.8#egg=ckan && \
  # Configure environment
  addgroup -g 92 ckan && \
  adduser -u 92 -h ${APP_DIR} -H -D -G ckan ckan && \
  cp ${CKAN_DIR}/who.ini ${APP_DIR} && \
  # Set timezone
  echo "UTC" >  /etc/timezone && \
  # Change ownership to app user
  chown -R ckan:ckan ${APP_DIR} && \
  # Remove unnecessary files
  rm -rf \
      ${APP_DIR}/wheels \
      ${CKAN_DIR}/.git

# Create entrypoint directory for children image scripts
ONBUILD RUN mkdir docker-entrypoint.d

# Create afterinit directory for children image scripts
ONBUILD RUN mkdir docker-afterinit.d

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD curl --fail http://localhost:5000/api/3/action/status_show || exit 1

USER ckan

CMD ["/srv/app/start_ckan.sh"]

#
# CKAN build
#
FROM base_ckan AS ckan_build

# switch from ckan to root user
USER root

ENV PROJ_DIR=/usr \
    SUPERV_DIR=${APP_DIR}/supervisor \
    CRON_DIR=${APP_DIR}/cron \
    SCRIPT_DIR=${APP_DIR}/scripts \
    TEMPLATE_DIR=${APP_DIR}/templates \
    EXT_DIR=${APP_DIR}/ckanext \
    WWW_DIR=/var/www

# Install required packages
RUN \
  apk add --no-cache \
      gcc \
      g++ \
      bash \
      patch \
      zip \
      unzip \
      rsync \
      proj-dev \
      proj-util \
      zlib-dev \
      jpeg-dev \
      geos-dev \
      libpq-dev \
      util-linux \
      nfs-utils && \
  pip install \
    jinja2-cli \
    supervisor \
    cryptography \
    ndg-httpsclient \
    pyasn1 \
    polib \
    botocore \
    "numpy < 2" \
    boto \
    boto3

# copy app files
COPY scripts ${SCRIPT_DIR}
COPY data ${DATA_DIR}_base
COPY templates ${TEMPLATE_DIR}
COPY supervisor ${SUPERV_DIR}
COPY cron ${CRON_DIR}
COPY src/ckan/patches ${SRC_DIR}/ckan/patches

# apply patches
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
#    patch --strip=1 --input=patches/fix_license_dictization.patch && \
    patch --strip=1 --input=patches/fix_truncate_helper_annotations.patch && \
    patch --strip=1 --input=patches/fix_use_default_schema_parameter.patch && \
    patch --strip=1 --input=patches/remove_tracking.patch && \
    patch --strip=1 --input=patches/remove_tracking_summary_from_solr_index.patch && \
    patch --strip=1 --input=patches/iauthenticator_fix.patch && \
    patch --strip=1 --input=patches/fix_templatehelpers_plugin_order.patch && \
    patch --strip=1 --input=patches/fix_server_error_on_group_pages.patch

RUN \
  # Make scripts executable
  chmod +x ${SCRIPT_DIR}/*.sh && \
  # Remove unused configuration
  rm -f ${APP_DIR}/ckan.ini && \
  rm -f ${APP_DIR}/who.ini && \
  # Add directory for static content
  mkdir -p ${WWW_DIR} && \
  # install crontab
  chmod +x ${CRON_DIR}/scripts/*.sh && \
  crontab -u ckan ${CRON_DIR}/crontab

# Install supercronic for running cronjobs in container

ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8 \
    SUPERCRONIC=supercronic-linux-amd64

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic


# Install qsv for ckanext-qa

ENV QSV_URL=https://github.com/dathere/qsv/releases/download/3.3.0/qsv-3.3.0-x86_64-unknown-linux-musl.zip \
    QSV_SHA1SUM=57f42781d57213416165bd6fcd366d0a20d4ec53 \
    QSV_ZIP=qsv-3.3.0-x86_64-unknown-linux-musl.zip \
    QSV=qsv

RUN curl -fsSLO "$QSV_URL" \
 && echo "${QSV_SHA1SUM}  ${QSV_ZIP}" | sha1sum -c - \
 && unzip "$QSV_ZIP" -d /tmp/qsv \
 && chmod +x "/tmp/qsv/$QSV" \
 && mv "/tmp/qsv/$QSV" "/usr/local/bin/$QSV"


#
# Development image (for local development)
#
FROM ckan_build AS ckan_development

ENV DEV_MODE=true

RUN \
  # install ckan dev requirements
  pip install -r ${SRC_DIR}/ckan/dev-requirements.txt && \
  pip install pytest-ckan && \
  # enable sudo for ckan user
  apk add --no-cache sudo && \
  addgroup sudo && \
  adduser ckan sudo && \
  echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
  # fix permissions
  chown -R ckan:ckan ${APP_DIR}


# switch from root to ckan user
USER ckan

ENTRYPOINT ["/srv/app/scripts/entrypoint_ckan.sh"]

#
# Modules build (for production)
#
FROM configured_base AS modules_build

# setup env vars:
ENV APP_DIR=/srv/app \
    EXT_DIR=${APP_DIR}/ckanext

# install required packages
RUN apk add --no-cache curl nodejs libjpeg

# Copy extensions
COPY ckanext/ ${EXT_DIR}/

# Add module configuration here

#
# Production image
#
FROM ckan_build AS production

# Install uwsgitop for stats analyzing
RUN pip install uwsgitop

# Install extension requirements (order in ascending probability of changes)
COPY ckanext/ckanext-forcetranslation/requirements.txt ${EXT_DIR}/ckanext-forcetranslation/requirements.txt
COPY ckanext/ckanext-archiver/requirements.txt ${EXT_DIR}/ckanext-archiver/requirements.txt
COPY ckanext/ckanext-dcat/requirements.txt ${EXT_DIR}/ckanext-dcat/requirements.txt
COPY ckanext/ckanext-drupal8/requirements.txt ${EXT_DIR}/ckanext-drupal8/requirements.txt
COPY ckanext/ckanext-hierarchy/requirements.txt ${EXT_DIR}/ckanext-hierarchy/requirements.txt
COPY ckanext/ckanext-spatial/requirements.txt ${EXT_DIR}/ckanext-spatial/requirements.txt
COPY ckanext/ckanext-statistics/requirements.txt ${EXT_DIR}/ckanext-statistics/requirements.txt
COPY ckanext/ckanext-matomo/requirements.txt ${EXT_DIR}/ckanext-matomo/requirements.txt
COPY ckanext/ckanext-fluent/requirements.txt ${EXT_DIR}/ckanext-fluent/requirements.txt
COPY ckanext/ckanext-qa/requirements.txt ${EXT_DIR}/ckanext-qa/requirements.txt
COPY ckanext/ckanext-showcase/requirements.txt ${EXT_DIR}/ckanext-showcase/requirements.txt
COPY ckanext/ckanext-report/requirements.txt ${EXT_DIR}/ckanext-report/requirements.txt
COPY ckanext/ckanext-sixodp_showcase/requirements.txt ${EXT_DIR}/ckanext-sixodp_showcase/requirements.txt
COPY ckanext/ckanext-sixodp_showcasesubmit/requirements.txt ${EXT_DIR}/ckanext-sixodp_showcasesubmit/requirements.txt
COPY ckanext/ckanext-ytp_recommendation/requirements.txt ${EXT_DIR}/ckanext-ytp_recommendation/requirements.txt
COPY ckanext/ckanext-ytp_tasks/requirements.txt ${EXT_DIR}/ckanext-ytp_tasks/requirements.txt
COPY ckanext/ckanext-harvest/requirements.txt ${EXT_DIR}/ckanext-harvest/requirements.txt
COPY ckanext/ckanext-cloudstorage/requirements.txt ${EXT_DIR}/ckanext-cloudstorage/requirements.txt
COPY ckanext/ckanext-organizationapproval/requirements.txt ${EXT_DIR}/ckanext-organizationapproval/requirements.txt
COPY ckanext/ckanext-advancedsearch/requirements.txt ${EXT_DIR}/ckanext-advancedsearch/requirements.txt
COPY ckanext/ckanext-apis/requirements.txt ${EXT_DIR}/ckanext-apis/requirements.txt
COPY ckanext/ckanext-ytp_main/requirements.txt ${EXT_DIR}/ckanext-ytp_main/requirements.txt
RUN ${SCRIPT_DIR}/install_extension_requirements.sh

# copy extensions
COPY --from=modules_build ${EXT_DIR} ${EXT_DIR}

RUN \
  # install extensions
  ${SCRIPT_DIR}/install_extensions.sh && \
  # fix permissions
  chown -R ckan:ckan ${APP_DIR}

# switch from root to ckan user
USER ckan

ENTRYPOINT ["/srv/app/scripts/entrypoint_ckan.sh"]
