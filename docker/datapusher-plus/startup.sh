# Define database urls
export SQLALCHEMY_DATABASE_URI=postgresql://${DB_DATAPUSHER_JOBS_USER}:${DB_DATAPUSHER_JOBS_PASS}@${DB_HOST}/${DB_DATAPUSHER_JOBS}
export WRITE_ENGINE_URL=postgresql://${DB_DATASTORE_USER}:${DB_DATASTORE_PASS}@${DB_HOST}/${DB_DATASTORE}

# Render environment variables to job configuration file
envsubst < ${SRC_DIR}/datapusher-plus/datapusher/.env.template > ${SRC_DIR}/datapusher-plus/datapusher/.env

# Run datapusher-plus
${VENV}/bin/uwsgi --socket=/tmp/uwsgi.sock --enable-threads -i ${CFG_DIR}/uwsgi.ini
