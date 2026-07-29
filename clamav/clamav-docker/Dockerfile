FROM clamav/clamav:1.4

RUN apk add --no-cache python3 py3-pip
RUN python -m venv /venv

COPY requirements.txt /
RUN source /venv/bin/activate && pip3 install -r /requirements.txt

COPY src/ /clamscan
COPY entrypoint.sh /entrypoint.sh

WORKDIR /clamscan
ENTRYPOINT ["/entrypoint.sh"]

