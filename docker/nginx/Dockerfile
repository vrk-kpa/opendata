# build args
ARG DYNATRACE_ENABLED=0

FROM nginx:1.23.2-alpine AS nginx_build

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
# Production stage, dynatrace enabled
#
FROM nginx_build AS production-dynatrace-1

# install dynatrace oneagent
# https://www.dynatrace.com/support/help/setup-and-configuration/setup-on-cloud-platforms/amazon-web-services/deploy-oneagent-on-aws-fargate
COPY --from=ayv41550.live.dynatrace.com/linux/oneagent-codemodules-musl:nginx / /
ENV LD_PRELOAD /opt/dynatrace/oneagent/agent/lib64/liboneagentproc.so

#
# Production stage, dynatrace disabled
#
FROM nginx_build AS production-dynatrace-0

# do nothing :^)

#
# Production image
#
FROM production-dynatrace-${DYNATRACE_ENABLED} AS production
