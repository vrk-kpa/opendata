# build args
ARG SECRET_NPMRC

#
# CKAN Base image
#

##################
### Build CKAN ###
##################
FROM public.ecr.aws/docker/library/python:3.9.16-alpine3.17 as base_ckan_build

# Set CKAN version to build
ENV GIT_URL=https://github.com/ckan/ckan.git
ENV GIT_BRANCH=ckan-2.9.9

# Set src dirs
ENV SRC_DIR=/srv/app/src
ENV PIP_SRC=${SRC_DIR}

# Create pip config
ENV PIP_CONFIG_FILE=${PIP_SRC}/pip.conf
COPY ./pip.conf ${PIP_CONFIG_FILE}

WORKDIR ${SRC_DIR}

# Packages to build CKAN requirements and plugins
RUN apk add --no-cache \
        bash \
        python3 \
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

# Create the src and pip cache directory
RUN mkdir -p ${SRC_DIR}

# Install pip
RUN curl -o ${SRC_DIR}/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python ${SRC_DIR}/get-pip.py

# Downgrade setuptools so that CKAN requirements can be built
RUN pip install setuptools==44.1.0

# Fetch and build CKAN and requirements
RUN pip install -e git+${GIT_URL}@${GIT_BRANCH}#egg=ckan
RUN rm -rf /srv/app/src/ckan/.git
RUN pip wheel --wheel-dir=/wheels -r ckan/requirements.txt
RUN pip wheel --wheel-dir=/wheels uWSGI==2.0.20 gevent==21.12.0 greenlet==1.1.3


###########################
### Default-Extensions ####
###########################
FROM public.ecr.aws/docker/library/python:3.9.16-alpine3.17 as base_extbuild

# Set src dirs
ENV SRC_DIR=/srv/app/src
ENV PIP_SRC=${SRC_DIR}

# List of default extensions
ENV DEFAULT_EXTENSIONS envvars

# Locations and tags, please use specific tags or revisions
ENV ENVVARS_GIT_URL=https://github.com/okfn/ckanext-envvars
ENV ENVVARS_GIT_BRANCH=0.0.1

RUN apk add --no-cache \
        python3 \
        python3-dev \
        git \
        curl

# Create the src directory
RUN mkdir -p ${SRC_DIR}

# Install pip
RUN curl -o ${SRC_DIR}/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python ${SRC_DIR}/get-pip.py

# Fetch and build the default CKAN extensions
RUN pip wheel --wheel-dir=/wheels git+${ENVVARS_GIT_URL}@${ENVVARS_GIT_BRANCH}#egg=ckanext-envvars

############
### MAIN ###
############
FROM public.ecr.aws/docker/library/python:3.9.16-alpine3.17 as base_ckan

ENV APP_DIR=/srv/app
ENV SRC_DIR=/srv/app/src
ENV CKAN_DIR=${SRC_DIR}/ckan
ENV DATA_DIR=/srv/app/data
ENV PIP_SRC=${SRC_DIR}
ENV CKAN_SITE_URL=http://localhost:5000
ENV CKAN__PLUGINS envvars image_view text_view recline_view datastore datapusher

ENV PIP_CONFIG_FILE=${PIP_SRC}/pip.conf
COPY ./pip.conf ${PIP_CONFIG_FILE}

# Install necessary packages to run CKAN
RUN apk add --no-cache \
        python3 \
        git \
        gettext \
        curl \
        postgresql-client \
        libmagic \
        pcre \
        libxslt \
        libxml2 \
        tzdata \
        apache2-utils && \
    # Create SRC_DIR
    mkdir -p ${SRC_DIR}

# Install pip
RUN curl -o ${SRC_DIR}/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python ${SRC_DIR}/get-pip.py

# Get artifacts from build stages
COPY --from=base_ckan_build /wheels /srv/app/wheels
COPY --from=base_extbuild /wheels /srv/app/ext_wheels
COPY --from=base_ckan_build /srv/app/src/ckan ${CKAN_DIR}

# Additional install steps for build stages artifacts
RUN pip install --no-index --find-links=/srv/app/wheels uWSGI==2.0.20 gevent==21.12.0

# Create a local user and group to run the app
RUN addgroup -g 92 ckan && \
    adduser -u 92 -h /srv/app -H -D -G ckan ckan

WORKDIR ${CKAN_DIR}

# Install CKAN
RUN pip install -e /srv/app/src/ckan && \
    cp who.ini ${APP_DIR} && \
    pip install --no-index --find-links=/srv/app/wheels -r requirements.txt && \
    # Install default CKAN extensions
    pip install --no-index --find-links=/srv/app/ext_wheels ckanext-envvars && \
    # Create and update CKAN config
    # Set timezone
    echo "UTC" >  /etc/timezone && \
    # Generate CKAN config
    ckan generate config ${APP_DIR}/production.ini && \
    ckan config-tool ${APP_DIR}/production.ini "beaker.session.secret = " && \
    # Configure plugins
    ckan config-tool ${APP_DIR}/production.ini "ckan.plugins = ${CKAN__PLUGINS}" && \
    # Create the data directory
    mkdir ${DATA_DIR} && \
    # Webassets can't be loaded from env variables at runtime, it needs to be in the config so that it is created
    ckan config-tool ${APP_DIR}/production.ini "ckan.webassets.path = ${DATA_DIR}/webassets" && \
    # Set the default level for extensions to INFO
    ckan config-tool ${APP_DIR}/production.ini -s logger_ckanext -e level=INFO && \
    # Change ownership to app user
    chown -R ckan:ckan /srv/app

# Remove wheels
RUN rm -rf /srv/app/wheels /srv/app/ext_wheels

# Copy necessary scripts
COPY setup/app ${APP_DIR}

WORKDIR ${APP_DIR}

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
FROM base_ckan as ckan_build

# switch from ckan to root user
USER root

ENV PROJ_DIR=/usr

# upgrade system + install required packages
RUN apk add --no-cache \
        gcc \
        g++ \
        libmagic \
        zlib-dev \
        jpeg-dev \
        geos-dev \
        bash \
        patch \
        zip \
        unzip \
        rsync \
        proj-dev \
        proj-util \
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
      numpy \
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
    patch --strip=1 --input=patches/add_prefix_to_werkzeug.patch

# install crontab
RUN chmod +x ${CRON_DIR}/scripts/*.sh && \
    crontab -u ckan ${CRON_DIR}/crontab


#
# Development image (for local development)
#
FROM ckan_build AS ckan_development

ENV DEV_MODE=true

# install ckan dev requirements
RUN pip install -r ${SRC_DIR}/ckan/dev-requirements.txt

# enable sudo for ckan user
RUN apk add sudo && \
    addgroup sudo && \
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
FROM public.ecr.aws/docker/library/python:3.9.16-alpine3.17 as modules_build

# install required packages
RUN apk add curl nodejs libjpeg

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
COPY ckanext/ckanext-sitesearch             ${EXT_DIR}/ckanext-sitesearch/
COPY ckanext/ckanext-ytp_recommendation     ${EXT_DIR}/ckanext-ytp_recommendation/


#
# Production image
#
FROM ckan_build AS production

# Install uwsgitop for stats analyzing
RUN pip install uwsgitop

# copy extensions
COPY --from=modules_build ${EXT_DIR} ${EXT_DIR}

# install extensions
RUN ${SCRIPT_DIR}/install_extensions.sh

# fix permissions
RUN chown -R ckan:ckan ${APP_DIR}

# switch from root to ckan user
USER ckan

ENTRYPOINT ["/srv/app/scripts/entrypoint_ckan.sh"]
