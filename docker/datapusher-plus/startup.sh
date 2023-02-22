# Render environment variables to job configuration file
envsubst < ${CFG_DIR}/.env.template > ${CFG_DIR}/.env

# Run datapusher-plus
${VENV}/bin/uwsgi --socket=/tmp/uwsgi.sock --enable-threads -i ${CFG_DIR}/uwsgi.ini --wsgi-file=${SRC_DIR}/datapusher-plus/wsgi.py
