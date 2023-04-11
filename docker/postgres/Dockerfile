FROM postgis/postgis:15-3.3

# allow all connections
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/data/pg_hba.conf

# include setup scripts
COPY ./docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
