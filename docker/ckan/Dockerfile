FROM ghcr.io/keitaroinc/ckan:2.9.4

# edit ckan config
RUN ckan config-tool ${APP_DIR}/production.ini "ckan.root_path = /data"
