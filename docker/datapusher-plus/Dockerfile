# Build datapusher+
FROM public.ecr.aws/docker/library/rust:alpine3.19 as cargo_build

RUN apk add build-base linux-headers
RUN cargo install qsv@0.130.0 --locked --bin qsvdp -F datapusher_plus,luau


#############################
### Build DataPusher Plus ###
#############################
FROM public.ecr.aws/docker/library/python:3.12.6-alpine3.19

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set Locale
ENV LC_ALL=en_US.UTF-8

ENV SRC_DIR=/srv/app/src
ENV VENV=/usr/lib/ckan/dpplus_venv
ENV CFG_DIR=/etc/ckan/datapusher-plus

WORKDIR ${SRC_DIR}

RUN apk add build-base linux-headers gettext curl py3-wheel uchardet

COPY --from=cargo_build /usr/local/cargo/bin/qsvdp /usr/local/bin

RUN python -m venv ${VENV}
RUN ${VENV}/bin/pip install uwsgi

ENV DATAPUSHER_COMMIT=89b6bb626d1a1f968438413749848dd2b73427fb

# Install DataPusher+ from repository, switch repository once latest PR on iconv has been merged
RUN wget https://github.com/Zharktas/datapusher-plus/archive/${DATAPUSHER_COMMIT}.zip -P /tmp
RUN unzip /tmp/${DATAPUSHER_COMMIT}.zip -d ${SRC_DIR} && mv ${SRC_DIR}/datapusher-plus-${DATAPUSHER_COMMIT} ${SRC_DIR}/datapusher-plus && rm /tmp/${DATAPUSHER_COMMIT}.zip
RUN cd ${SRC_DIR}/datapusher-plus && \
    ${VENV}/bin/pip install -r requirements-dev.txt && \
    ${VENV}/bin/pip install -e .

# Prepare configuration template (instantiation in startup.sh because of environment variables)
RUN adduser -S www-data
RUN mkdir -p ${CFG_DIR}
COPY ./environment ${SRC_DIR}/datapusher-plus/datapusher/.env.template
RUN touch ${SRC_DIR}/datapusher-plus/datapusher/.env && chown www-data ${SRC_DIR}/datapusher-plus/datapusher/.env
ENV JOB_CONFIG=${SRC_DIR}/datapusher-plus/datapusher/.env

RUN cp ${SRC_DIR}/datapusher-plus/deployment/datapusher-uwsgi.ini ${CFG_DIR}/uwsgi.ini
COPY ./startup.sh /startup.sh

USER www-data

ENTRYPOINT ["/bin/sh", "/startup.sh"]

EXPOSE ${DATAPUSHER_PORT}
