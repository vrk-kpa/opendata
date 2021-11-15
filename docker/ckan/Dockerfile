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
COPY modules/ytp-assets-common              /opt/ckan_extensions/ytp-assets-common/
COPY modules/ckanext-drupal8                /opt/ckan_extensions/ckanext-drupal8/
COPY modules/ckanext-ytp_drupal             /opt/ckan_extensions/ckanext-ytp_drupal/
COPY modules/ckanext-ytp_tasks              /opt/ckan_extensions/ckanext-ytp_tasks/
COPY modules/ckanext-ytp_request            /opt/ckan_extensions/ckanext-ytp_request/
COPY modules/ckanext-ytp_main               /opt/ckan_extensions/ckanext-ytp_main/
COPY modules/ckanext-hierarchy              /opt/ckan_extensions/ckanext-hierarchy/
COPY modules/ckanext-matomo                 /opt/ckan_extensions/ckanext-matomo/
COPY modules/ckanext-datarequests           /opt/ckan_extensions/ckanext-datarequests/
COPY modules/ckanext-harvest                /opt/ckan_extensions/ckanext-harvest/
COPY modules/ckanext-report                 /opt/ckan_extensions/ckanext-report/
COPY modules/ckanext-spatial                /opt/ckan_extensions/ckanext-spatial/
COPY modules/ckanext-dcat                   /opt/ckan_extensions/ckanext-dcat/
COPY modules/ckanext-cloudstorage           /opt/ckan_extensions/ckanext-cloudstorage/
COPY modules/ckanext-scheming               /opt/ckan_extensions/ckanext-scheming/
COPY modules/ckanext-fluent                 /opt/ckan_extensions/ckanext-fluent/
COPY modules/ckanext-showcase               /opt/ckan_extensions/ckanext-showcase/
COPY modules/ckanext-sixodp_showcase        /opt/ckan_extensions/ckanext-sixodp_showcase/
COPY modules/ckanext-sixodp_showcasesubmit  /opt/ckan_extensions/ckanext-sixodp_showcasesubmit/
COPY modules/ckanext-geoview                /opt/ckan_extensions/ckanext-geoview/
COPY modules/ckanext-pdfview                /opt/ckan_extensions/ckanext-pdfview/
COPY modules/ckanext-disqus                 /opt/ckan_extensions/ckanext-disqus/
COPY modules/ckanext-reminder               /opt/ckan_extensions/ckanext-reminder/
COPY modules/ckanext-archiver               /opt/ckan_extensions/ckanext-archiver/
COPY modules/ckanext-qa                     /opt/ckan_extensions/ckanext-qa/
COPY modules/ckanext-organizationapproval   /opt/ckan_extensions/ckanext-organizationapproval/
COPY modules/ckanext-advancedsearch         /opt/ckan_extensions/ckanext-advancedsearch/
COPY modules/ckanext-forcetranslation       /opt/ckan_extensions/ckanext-forcetranslation/
COPY modules/ckanext-apis                   /opt/ckan_extensions/ckanext-apis/
COPY modules/ckanext-prh_tools              /opt/ckan_extensions/ckanext-prh_tools/
COPY modules/ckanext-openapiviewer          /opt/ckan_extensions/ckanext-openapiviewer/
COPY modules/ckanext-statistics             /opt/ckan_extensions/ckanext-statistics/
COPY modules/ckanext-sentry                 /opt/ckan_extensions/ckanext-sentry/

# frontend requires some common components
COPY modules/avoindata-drupal-header        /opt/ckan_extensions/avoindata-drupal-header/

# set workdir, copy default package.json, import .npmrc as secret and run build script
# NOTE: SECRET_NPMRC arg is only for local development use, for production use buildkit secrets
WORKDIR /opt/ckan_extensions/ytp-assets-common
COPY docker/package.default.json /opt/ckan_extensions/ytp-assets-common/package.default.json
COPY --chmod=+x docker/build_frontend.sh /opt/ckan_extensions/ytp-assets-common/build_frontend.sh
ARG SECRET_NPMRC
RUN --mount=type=secret,id=npmrc ./build_frontend.sh

#
# CKAN build
#
FROM ghcr.io/keitaroinc/ckan:2.8.9-focal

# switch to root
USER root

# install required packages & downgrade python setuptools + install python packages
RUN apt-get update -yq && \
    apt-get install build-essential \
                    libpq-dev \
                    libxslt1-dev \
                    zlib1g-dev \
                    libgeos-c1v5 \
                    libxml2 \
                    libxml2-dev \
                    unzip \
                    zip \
                    libssl-dev \
                    libffi-dev \
                    postgresql-client \
                    cron \
                    rsync \
                    -yq && \
    pip install cryptography pyOpenSSL ndg-httpsclient pyasn1 jinja2-cli polib

# install custom modules
ENV EXT_DIR=/opt/ckan_extensions
COPY --from=frontend_builder /opt/ckan_extensions ${EXT_DIR}/

# install static resources
ENV WWW_DIR=/var/www
ENV RES_DIR=${WWW_DIR}/resources
RUN mkdir -p ${WWW_DIR} && mv ${EXT_DIR}/ytp-assets-common/resources ${WWW_DIR}/

# install extension dependencies
RUN pip install -r ${EXT_DIR}/ckanext-drupal8/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-ytp_tasks/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-ytp_main/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-matomo/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-harvest/pip-requirements.txt && \
#    pip install -r ${EXT_DIR}/ckanext-report/requirements.txt && \ CKAN 2.9.4 + Python 3 req
    pip install -r ${EXT_DIR}/ckanext-spatial/pip-requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-dcat/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-scheming/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-sixodp_showcase/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-sixodp_showcasesubmit/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-geoview/pip-requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-archiver/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-qa/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-organizationapproval/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-advancedsearch/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-forcetranslation/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-apis/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-prh_tools/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-statistics/requirements.txt && \
    pip install -r ${EXT_DIR}/ckanext-sentry/requirements.txt

# install extensions
RUN pip install -e ${EXT_DIR}/ckanext-drupal8 && \
    pip install -e ${EXT_DIR}/ckanext-ytp_drupal && \
    pip install -e ${EXT_DIR}/ckanext-ytp_tasks && \
    pip install -e ${EXT_DIR}/ckanext-ytp_request && \
    pip install -e ${EXT_DIR}/ckanext-ytp_main && \
    pip install -e ${EXT_DIR}/ckanext-hierarchy && \
    pip install -e ${EXT_DIR}/ckanext-matomo && \
    pip install -e ${EXT_DIR}/ckanext-datarequests && \
    pip install -e ${EXT_DIR}/ckanext-harvest && \
    pip install -e ${EXT_DIR}/ckanext-report && \
    pip install -e ${EXT_DIR}/ckanext-spatial && \
    pip install -e ${EXT_DIR}/ckanext-dcat && \
    pip install -e ${EXT_DIR}/ckanext-cloudstorage && \
    pip install -e ${EXT_DIR}/ckanext-scheming && \
    pip install -e ${EXT_DIR}/ckanext-fluent && \
    pip install -e ${EXT_DIR}/ckanext-showcase && \
    pip install -e ${EXT_DIR}/ckanext-sixodp_showcase && \
    pip install -e ${EXT_DIR}/ckanext-sixodp_showcasesubmit && \
    pip install -e ${EXT_DIR}/ckanext-geoview && \
    pip install -e ${EXT_DIR}/ckanext-pdfview && \
    pip install -e ${EXT_DIR}/ckanext-disqus && \
    pip install -e ${EXT_DIR}/ckanext-reminder && \
    pip install -e ${EXT_DIR}/ckanext-archiver && \
    pip install -e ${EXT_DIR}/ckanext-qa && \
    pip install -e ${EXT_DIR}/ckanext-organizationapproval && \
    pip install -e ${EXT_DIR}/ckanext-advancedsearch && \
    pip install -e ${EXT_DIR}/ckanext-forcetranslation && \
    pip install -e ${EXT_DIR}/ckanext-apis && \
    pip install -e ${EXT_DIR}/ckanext-prh_tools && \
    pip install -e ${EXT_DIR}/ckanext-openapiviewer && \
    pip install -e ${EXT_DIR}/ckanext-statistics && \
    pip install -e ${EXT_DIR}/ckanext-sentry

# compile extension translations
RUN cd ${EXT_DIR}/ckanext-ytp_request && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-ytp_drupal && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-ytp_main && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-sixodp_showcase && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-report && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-organizationapproval && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-advancedsearch && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-scheming && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-statistics && python setup.py compile_catalog -f && \
    cd ${EXT_DIR}/ckanext-datarequests && python setup.py compile_catalog -f

# install scripts
COPY --chmod=+x docker/ckan/scripts/ ${APP_DIR}/

WORKDIR ${SRC_DIR}/ckan

# apply patches
COPY docker/ckan/patches ${SRC_DIR}/ckan/patches
RUN patch --strip=1 --input=patches/enable_multiple_image_uploads.patch && \
    patch --strip=1 --input=patches/remove-ckan-fontawesome.patch && \
    patch --strip=1 --input=patches/enforce-url-decoding.patch && \
    patch --strip=1 --input=patches/add_error_email_logger_to_flask.patch && \
    patch --strip=1 --input=patches/add_credentials_to_email_logger.patch && \
    patch --strip=1 --input=patches/remove_deprecated_resource_preview_call.patch && \
    patch --strip=1 --input=patches/remove_members_from_group_read.patch && \
    patch --strip=1 --input=patches/remove_user_activity_from_group_activity_list.patch && \
    patch --strip=1 --input=patches/optimize_group_show.patch && \
    patch --strip=1 --input=patches/optimize_template_loading.patch && \
    patch --strip=1 --input=patches/group_include_extras.patch && \
    patch --strip=1 --input=patches/group_admin_protection.patch && \
    patch --strip=1 --input=patches/remove_gravatar.patch && \
    patch --strip=1 --input=patches/json_serializable_lazyjsonobject.patch && \
    patch --strip=1 --input=patches/implement_is_required_for_image_upload.patch && \
    patch --strip=1 --input=patches/add_drafts_to_search.patch && \
    patch --strip=1 --input=patches/add_group_extra_resource_db_indices.patch && \
    patch --strip=1 --input=patches/add_cache_control_headers_to_flask.patch && \
    patch --strip=1 --input=patches/fix_invalid_search_facets_template_error.patch && \
    patch --strip=1 --input=patches/remove_stacktraces_from_http_errors.patch

WORKDIR ${APP_DIR}

# install data for CKAN UI options
COPY docker/ckan/data ${DATA_DIR}

# install templates
COPY docker/ckan/templates ${APP_DIR}/templates

# install crontab
COPY --chown=ckan:ckan docker/ckan/cron/crontab /home/ckan/cron.d/crontab
COPY --chmod=+x --chown=ckan:ckan docker/ckan/cron/scripts /opt/cron_scripts/
RUN crontab -u ckan /home/ckan/cron.d/crontab && chmod u+s /usr/sbin/cron

# finalize installation
RUN rm -f ${APP_DIR}/production.ini && \
    rm -f ${APP_DIR}/who.ini && \
    chown -R ckan:ckan /srv/app

# setup shared base directories
RUN mkdir -p /opt/base && \
    mv /srv/app/data /opt/base/data && \
    mv /var/www/resources /opt/base/resources && \
    chown -R ckan:ckan /opt/base/data && \
    chown -R ckan:ckan /opt/base/resources

# make sure permissions are correct
RUN mkdir -p /srv/app/data && \
    mkdir -p /var/www/resources && \
    chown -R ckan:ckan /srv/app/data && \
    chown -R ckan:ckan /var/www/resources

# switch back to ckan
USER ckan

ENTRYPOINT ["/srv/app/entrypoint_ckan.sh"]
