#!/bin/bash
set -e

echo "init_filesystems() ..."

# check if migration fs is mounted, migrate data if it is
if [[ -d "/mnt/ytp_files/ckan" ]]; then
  echo "migrating data from /mnt/ytp_files/ckan to /srv/app/data ..."
  rsync -au --chown=ckan:ckan /mnt/ytp_files/ckan/ /srv/app/data
  echo "printing migration source contents ..."
  ls -lah /mnt/ytp_files/ckan
  echo "printing migration destination contents ..."
  ls -lah /srv/app/data
fi

# init mounted filesystems (ECS Fargate EFS limitation forces this approach)
echo "initializing /srv/app/data & /var/www/resources ..."
rsync -au /opt/base/data/ /srv/app/data &
rsync -au --delete /opt/base/resources/ /var/www/resources --exclude=.init-progress &
wait
