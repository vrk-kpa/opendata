# build args

FROM nginx:1.25.2-alpine AS nginx_build

# install pkgs
RUN apk add --update-cache python3 py3-pip && \
    pip install jinja2-cli

# copy config, nginx templated configs & jinja2 templates
COPY nginx.conf /etc/nginx/nginx.conf
COPY templates /etc/nginx/templates
COPY jinja2-templates /etc/nginx/jinja2-templates

# install entrypoint scripts
COPY docker-entrypoint.d/100-install-jinja2-templates.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/*.sh

# install www directory
COPY www /var/www/


#
# Production image
#
FROM nginx_build AS production
