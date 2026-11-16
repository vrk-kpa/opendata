FROM postgres:18@sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6

# allow all connections
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/pg_hba.conf

# include setup scripts
COPY ./docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
