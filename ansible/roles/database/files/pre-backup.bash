#! /bin/bash

. /etc/default/autopostgresqlbackup

DATE=`date +%Y-%m-%d`
DOW=`date +%A`
NEW_DATE=`date --iso-8601=seconds`

shopt -s nullglob

for backup in $BACKUPDIR/daily/*/*_$DATE_*.$DOW.sql*; do
        backup_path=`dirname $backup`
        mv "$backup" "$backup_path/$NEW_DATE.sql.gz"
done

shopt -u nullglob
