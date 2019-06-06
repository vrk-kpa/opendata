#!/bin/sh
set -e

"$@"

echo "Waiting for logs to be flushed to Cloudwatch"
sleep 10

exit $?