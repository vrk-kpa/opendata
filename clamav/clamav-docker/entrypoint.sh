#!/bin/sh

source /venv/bin/activate
python -u app.py

echo "Waiting for logs to be flushed to Cloudwatch"
sleep 10
