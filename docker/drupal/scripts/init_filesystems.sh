#!/bin/sh
set -e

echo "init_filesystems() ..."

# init mounted filesystems (ECS Fargate EFS limitation forces this approach)
rsync -au /opt/base/web/ /opt/drupal/web
rsync -au /opt/base/resources/ /var/www/resources
