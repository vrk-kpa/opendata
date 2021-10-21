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
COPY modules /opt/ckan_extensions/

# set workdir to frontend module & copy package.json
WORKDIR /opt/ckan_extensions/ytp-assets-common
COPY docker/package.default.json /opt/ckan_extensions/ytp-assets-common/package.json

# build frontend
RUN npm install --unsafe-perm=true --allow-root && gulp

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

# install override requirements
# TODO: why is this done in the ansible playbook??
#RUN pip install flask==0.12 flask-login==0.3.0 simplejson==3.16.0 six==1.13.0 pyOpenSSL==20.0.0 psycopg2==2.8.6

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

WORKDIR ${SRC_DIR}

# apply patches
COPY docker/ckan/patches ${SRC_DIR}/ckan/patches
RUN ${SRC_DIR}/ckan/patches.sh

WORKDIR ${APP_DIR}

# install data for CKAN UI options
COPY docker/ckan/data ${DATA_DIR}

# install templates
COPY docker/ckan/templates ${APP_DIR}/templates

# finalize installation
RUN rm -f ${APP_DIR}/production.ini && \
    rm -f ${APP_DIR}/who.ini && \
    chown -R ckan:ckan /srv/app

# switch back to ckan
USER ckan
