FROM clamav/clamav:1.4@sha256:982e28f90061d0e66eb03276419f589a47c9fa601e985e472fc2f6c64b497ca0

RUN apk add --no-cache python3 py3-pip
RUN python -m venv /venv

COPY requirements.txt /
RUN source /venv/bin/activate && pip3 install -r /requirements.txt

COPY src/ /clamscan
COPY entrypoint.sh /entrypoint.sh

WORKDIR /clamscan
ENTRYPOINT ["/entrypoint.sh"]

