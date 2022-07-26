#!/bin/bash
set -e

# source env
. /srv/app/cron/.environment

echo "job started: prh-stop"

# run commands
PROCESS_IDS=$(pgrep start-prh-crawl)
if [ ! -z "$PROCESS_IDS" ]; then
  pkill -9 -P $PROCESS_IDS
fi
