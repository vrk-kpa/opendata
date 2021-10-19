FROM ubuntu:focal AS builder

# install required packages
RUN apt-get update -yq && apt-get install curl libjpeg-turbo8 build-essential autoconf -yq

# install nodejs via nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -yq nodejs && npm install -g gulp

# copy custom modules
COPY modules                            /opt/modules/

# set workdir to frontend module
WORKDIR /opt/modules/ytp-assets-common

# use package.free.json as default
RUN mv ./package.json ./package.paid.json
COPY docker/modules/package.free.json    /opt/modules/ytp-assets-common/package.json

# build custom theme
RUN npm install --unsafe-perm=true --allow-root && gulp

# setup package.json files for runtime usage
RUN mv ./package.json ./package.free.json

# set workdir to root & install entrypoint.sh
WORKDIR /
COPY docker/modules/scripts/ ./
RUN chmod +x *.sh

ENTRYPOINT ["./entrypoint.sh"]
