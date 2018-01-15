#!/bin/sh

# Update all submodules to separate projects. Execute at ..

if [ "$0" != "./scripts/update.sh" ]; then
    echo "Run at ytp root: ./scripts/update.sh"
    exit 1
fi

for module in ckanext-ytp_main ytp-drupal-user; do
    git remote add $module https://github.com/yhteentoimivuuspalvelut/$module.git
    git fetch $module
    git subtree push --prefix=modules/$module $module master
done
