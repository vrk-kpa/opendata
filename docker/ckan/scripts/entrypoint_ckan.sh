#!/bin/bash
set -e

# set the common uwsgi options
export UWSGI_OPTS="--socket /tmp/uwsgi.sock --uid 92 --gid 92 --http :5000 --master --enable-threads --paste config:/srv/app/production.ini --paste-logger /srv/app/production.ini --lazy-apps --gevent 2000 -p 2 -L --gevent-early-monkey-patch"

# init ckan if not done, otherwise run re-init
if [ ! -f ${DATA_DIR}/.init-done ]; then
  flock -x ${DATA_DIR}/.init-lock -c './init_ckan.sh'

  # set init flag to done
  touch ${DATA_DIR}/.init-done
else
  flock -x ${DATA_DIR}/.init-lock -c './reinit_ckan.sh'
fi

# run uwsgi
uwsgi $UWSGI_OPTS
