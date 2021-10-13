# build nginx
FROM nginx:1.21-alpine

# copy configs
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./templates /etc/nginx/templates

# symlink resources (must be mounted)
RUN mkdir -p /var/www && ln -sf /opt/modules/ytp-assets-common/resources/    /var/www/resources
