#!/bin/sh
set -e

# remove init flag if exists
rm -f /opt/modules/.init-done

# choose package.json file based on setup
cd /opt/modules/ytp-assets-common
if [ -f ./.npmrc ] && [ -s ./.npmrc ]; then
  echo "found .npmrc, attempting rebuild with fontawesome full version..."

  # swap package.json file
  rm -f package.json && cp package.paid.json package.json

  # rebuild custom theme
  rm -rf ./resources/*
  npm install --unsafe-perm=true --allow-root
  gulp
else
  echo "no .npmrc found, using the pre-built frontend with fontawesome free version..."
fi

# set init flag to done
touch /opt/modules/.init-done

echo "all done!"
