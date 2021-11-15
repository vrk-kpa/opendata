#!/bin/bash
set -e

echo "init_filesystems() ..."

# init mounted filesystems (ECS Fargate EFS limitation forces this approach)
rsync -au /opt/base/data/ /srv/app/data
rsync -au --delete /opt/base/resources/ /var/www/resources --exclude=.init-progress
