FROM mkodockx/docker-clamav
RUN apt-get update && apt-get install -y python3 python3-pip && pip3 install clamd boto3
COPY clamscan.py /
CMD ["python3", "-u", "clamscan.py"]