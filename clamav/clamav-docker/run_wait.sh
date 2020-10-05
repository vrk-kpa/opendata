#!/bin/sh
set -e

sudo service clamav-daemon restart

"$@"

echo "Waiting for logs to be flushed to Cloudwatch"
sleep 10

exit $?
