#############################
### Build DataPusher Plus ###
#############################
FROM public.ecr.aws/docker/library/python:3.10.9-alpine3.17

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set Locale
ENV LC_ALL=en_US.UTF-8

ENV SRC_DIR=/srv/app/src
ENV VENV=/usr/lib/ckan/dpplus_venv
ENV CFG_DIR=/etc/ckan/datapusher-plus

WORKDIR ${SRC_DIR}

RUN apk add build-base linux-headers git gettext

#install qsv;
RUN wget https://github.com/jqnatividad/qsv/releases/download/0.87.1/qsv-0.87.1-x86_64-unknown-linux-musl.zip -P /tmp
RUN unzip /tmp/qsv-0.87.1-x86_64-unknown-linux-musl.zip -d /tmp
RUN rm /tmp/qsv-0.87.1-x86_64-unknown-linux-musl.zip
RUN mv /tmp/qsv* /usr/local/bin

#python env setup; link python3 to python cmd; make venv; install uwsgi;
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN python -m venv ${VENV}
RUN ${VENV}/bin/pip install uwsgi


# Install DataPusher+ from repository
RUN git clone https://github.com/dathere/datapusher-plus.git --depth 1 --branch 0.10.1
RUN cd ${SRC_DIR}/datapusher-plus && \
    ${VENV}/bin/pip install -r requirements-dev.txt && \
    ${VENV}/bin/pip install -e .

# Prepare configuration template (instantiation in startup.sh because of environment variables)
RUN adduser -S www-data
RUN mkdir -p ${CFG_DIR}
COPY ./environment ${CFG_DIR}/.env.template
RUN touch ${CFG_DIR}/.env && chown www-data ${CFG_DIR}/.env
ENV JOB_CONFIG=${CFG_DIR}/.env

RUN cp ${SRC_DIR}/datapusher-plus/deployment/datapusher-uwsgi.ini ${CFG_DIR}/uwsgi.ini
COPY ./startup.sh /startup.sh

USER www-data

ENTRYPOINT ["/bin/sh", "/startup.sh"]

EXPOSE ${DATAPUSHER_PORT}
