#!/bin/sh

# Ensure clamav user owns the data directory
chown -R clamav:clamav /var/lib/clamav

source /venv/bin/activate
python -u app.py

echo "Waiting for logs to be flushed to Cloudwatch"
sleep 10
