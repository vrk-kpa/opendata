FROM postgis/postgis:10-3.0

# allow all connections
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/data/pg_hba.conf

# include setup scripts
COPY ./docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
