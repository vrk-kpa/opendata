#!/bin/bash
set -eo pipefail

# NOTE: this file is executed by BuildKit secrets system
#       this means that the secrets won't be leaked into
#       the final image.
# NOTE: for local development, build ARGs are used instead!

if [[ -s /run/secrets/npmrc ]]; then
  echo "importing secret .npmrc..."
  cat /run/secrets/npmrc > .npmrc
elif [[ ! -z "$SECRET_NPMRC" ]]; then
  echo "WARNING: importing secret .npmrc data from build ARG..."
  echo "WARNING: this is only meant for local development!"
  echo "$SECRET_NPMRC" > .npmrc
else
  echo "secret .npmrc not available, using default package.json..."
  mv -f package.default.json package.json
fi

# build & cleanup
npm install --unsafe-perm=true --allow-root && \
  npm run gulp && \
  rm -f .npmrc && \
  rm -rf node_modules
