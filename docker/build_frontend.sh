#!/bin/bash
set -euo pipefail

# NOTE: this file is executed by BuildKit secrets system
#       this means that the secrets won't be leaked into
#       the final image.

if [ -s /run/secrets/npmrc ]; then
  echo "importing secret .npmrc..."
  cat /run/secrets/npmrc > .npmrc
else
  echo "secret .npmrc not available, using default package.json..."
  rm -f package.json
  mv package.default.json package.json
fi

npm install --unsafe-perm=true --allow-root && gulp
