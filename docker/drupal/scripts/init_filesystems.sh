#!/bin/bash
set -e

echo "init_filesystems() ..."

# init mounted filesystems (ECS Fargate EFS limitation forces this approach)
echo "initializing /opt/drupal/web & /var/www/resources ..."
rsync -au /opt/base/web/ /opt/drupal/web &
rsync -au --delete /opt/base/resources/ /var/www/resources --exclude=.init-progress &
wait
